"""Simple indexer that listens for contract events and persists them to the DB.

Usage: python indexer/indexer.py --rpc http://localhost:8545 --contract-address 0x... --abi ../artifacts/contracts/MilestoneFunding.sol/MilestoneFunding.json
"""
import argparse
import json
import logging
import time
import sys
import uuid
from web3 import Web3
from sqlalchemy import select
from db import get_session
from models import Transaction
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from pythonjsonlogger import jsonlogger

# Structured JSON logging to stdout
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('indexer')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Prometheus metrics
EVENTS_PROCESSED = Counter('indexer_events_processed_total', 'Total processed events')
EVENTS_DUPLICATE = Counter('indexer_events_duplicate_total', 'Total duplicate events skipped')
EVENTS_ERRORS = Counter('indexer_events_errors_total', 'Total processing errors')
EVENT_PROCESS_DURATION = Histogram('indexer_event_process_duration_seconds', 'Event processing duration seconds')
LAST_PROCESSED_BLOCK = Gauge('indexer_last_processed_block', 'Last block number processed by indexer')



def process_transaction_event(event, session):
    # idempotent insert based on tx hash
    tx_hash = event['transactionHash'].hex()
    trace_id = uuid.uuid4().hex
    try:
        existing = session.execute(select(Transaction).where(Transaction.tx_hash == tx_hash)).scalar_one_or_none()
        if existing:
            EVENTS_DUPLICATE.inc()
            logger.info('duplicate_event', extra={'tx_hash': tx_hash, 'trace_id': trace_id})
            return False

        args = event['args']
        project_id = args.get('projectId') if 'projectId' in args else None
        amount = args.get('amount') if 'amount' in args else 0

        start = time.time()
        t = Transaction(tx_hash=tx_hash, user_id=1, project_id=project_id, amount=Web3.fromWei(amount, 'ether'))
        session.add(t)
        session.commit()
        duration = time.time() - start
        EVENT_PROCESS_DURATION.observe(duration)
        EVENTS_PROCESSED.inc()
        # structured log with trace id
        logger.info('persisted_transaction', extra={'tx_hash': tx_hash, 'duration_s': duration, 'trace_id': trace_id})
        return True
    except Exception as e:
        EVENTS_ERRORS.inc()
        logger.exception('error_persisting_transaction', extra={'tx_hash': tx_hash, 'trace_id': trace_id, 'error': str(e)})
        return False


def listen_loop(w3, contract):
    logger.info('Starting event listener...')
    last_block = w3.eth.block_number
    logger.info('Current block %s', last_block)
    # update last processed block metric
    LAST_PROCESSED_BLOCK.set(last_block)
    # create HTTP metrics server on provided port (default 8003)
    metrics_port = int(getattr(listen_loop, '_metrics_port', 8003))
    start_http_server(metrics_port)
    logger.info('metrics_exposed', extra={'port': metrics_port})

    event_filter = contract.events.TransactionCreated.createFilter(fromBlock='latest')
    with get_session() as session:
        while True:
            for ev in event_filter.get_new_entries():
                try:
                    process_transaction_event(ev, session)
                except Exception as e:
                    logger.exception('Error processing event: %s', e)
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpc', required=True)
    parser.add_argument('--contract-address', required=True)
    parser.add_argument('--abi', required=True)
    parser.add_argument('--metrics-port', type=int, default=8003, help='Prometheus metrics HTTP port')
    args = parser.parse_args()
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    with open(args.abi, 'r') as f:
        data = json.load(f)
        abi = data.get('abi', data)
    contract = w3.eth.contract(address=args.contract_address, abi=abi)
    setattr(listen_loop, '_metrics_port', args.metrics_port)
    listen_loop(w3, contract)


if __name__ == '__main__':
    main()

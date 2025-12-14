"""Backfill worker to read historical logs and persist events.

Usage: python indexer/backfill.py --rpc <rpc> --contract <addr> --abi <abi.json> --from 0 --to latest
"""
import argparse
import json
import logging
import time
import sys
from web3 import Web3
from db import get_session
from models import Transaction
from prometheus_client import Counter, Histogram, start_http_server
from pythonjsonlogger import jsonlogger

# structured JSON logging
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('backfill')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Prometheus metrics
BACKFILL_PERSISTED = Counter('backfill_events_persisted_total', 'Total events persisted by backfill')
BACKFILL_DUPLICATES = Counter('backfill_events_duplicate_total', 'Total duplicate events skipped by backfill')
BACKFILL_ERRORS = Counter('backfill_errors_total', 'Backfill processing errors')
BACKFILL_DURATION = Histogram('backfill_duration_seconds', 'Backfill total duration seconds')


def backfill(w3, contract, from_block, to_block):
    logger.info(f'Backfill {from_block} -> {to_block}', extra={'from_block': from_block, 'to_block': to_block})
    start_time = time.time()
    metrics_port = int(getattr(backfill, '_metrics_port', 8003))
    start_http_server(metrics_port)
    logger.info('metrics_exposed', extra={'port': metrics_port})
    events = contract.events.TransactionCreated().get_logs(fromBlock=from_block, toBlock=to_block)
    persisted = 0
    try:
        with get_session() as s:
            for ev in events:
                tx_hash = ev['transactionHash'].hex()
                exists = s.query(Transaction).filter_by(tx_hash=tx_hash).first()
                if exists:
                    BACKFILL_DUPLICATES.inc()
                    logger.info('skip_duplicate', extra={'tx_hash': tx_hash})
                    continue
                args = ev['args']
                amount = args.get('amount', 0)
                t = Transaction(tx_hash=tx_hash, user_id=1, project_id=args.get('projectId'), amount=Web3.fromWei(amount, 'ether'))
                s.add(t)
                persisted += 1
            s.commit()
    except Exception as e:
        BACKFILL_ERRORS.inc()
        logger.exception('backfill_error', extra={'error': str(e)})
    duration = time.time() - start_time
    BACKFILL_PERSISTED.inc(persisted)
    BACKFILL_DURATION.observe(duration)
    logger.info('backfill_complete', extra={'persisted': persisted, 'duration_s': duration})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpc', required=True)
    parser.add_argument('--contract', required=True)
    parser.add_argument('--abi', required=True)
    parser.add_argument('--from', dest='from_block', default=0, type=int)
    parser.add_argument('--to', dest='to_block', default='latest')
    parser.add_argument('--metrics-port', type=int, default=8003, help='Prometheus metrics HTTP port')
    args = parser.parse_args()
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    with open(args.abi, 'r') as f:
        data = json.load(f)
        abi = data.get('abi', data)
    contract = w3.eth.contract(address=args.contract, abi=abi)
    to_block = w3.eth.block_number if args.to_block == 'latest' else int(args.to_block)
    setattr(backfill, '_metrics_port', args.metrics_port)
    backfill(w3, contract, args.from_block, to_block)


if __name__ == '__main__':
    main()

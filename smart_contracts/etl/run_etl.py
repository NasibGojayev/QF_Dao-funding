import argparse
import os
from db import init_db
from contracts import GRANT_REGISTRY_ABI, GRANT_REGISTRY_ADDRESS
from web3 import Web3
from backfill import run_backfill
from listener import run_listener
from logger import setup_logger

logger = setup_logger(__name__)

# Connect to local Hardhat node
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
contract = w3.eth.contract(address=GRANT_REGISTRY_ADDRESS, abi=GRANT_REGISTRY_ABI)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL Bridge for GrantRegistry smart contract")
    parser.add_argument("mode", choices=["backfill", "listener"], help="ETL mode to run")
    parser.add_argument("--start-block", type=int, default=0, help="Start block for backfill (default: 0)")
    parser.add_argument("--end-block", type=int, help="End block for backfill (default: latest)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for backfill (default: 1000)")
    parser.add_argument("--poll-interval", type=int, default=2, help="Poll interval for listener in seconds (default: 2)")
    
    args = parser.parse_args()
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Check connection
    if not w3.is_connected():
        logger.error("Failed to connect to Ethereum node at http://127.0.0.1:8545")
        exit(1)
    
    logger.info(f"Connected to Ethereum node. Current block: {w3.eth.block_number}")
    
    # Run selected mode
    if args.mode == "backfill":
        end_block = args.end_block if args.end_block else w3.eth.block_number
        logger.info(f"Running backfill mode from block {args.start_block} to {end_block}")
        run_backfill(contract, "ProposalCreated", args.start_block, end_block, args.batch_size)
    else:
        logger.info("Running listener mode")
        run_listener(contract, "ProposalCreated", args.poll_interval)


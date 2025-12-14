
import os
import json
import time
from django.conf import settings
from web3 import Web3
# from django.core.management import setup_environ  <-- Removed

# Setup Django standalone
import sys
sys.path.append('/Users/nasibgojayev/Desktop/visual_programming/backend/doncoin')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from base.models import Proposal

def run():
    # Load Env
    from dotenv import load_dotenv
    load_dotenv('/Users/nasibgojayev/Desktop/visual_programming/.env')
    
    HTTP_PROVIDER = os.getenv('HARDHAT_RPC_URL', "http://127.0.0.1:8545")
    w3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER))
    
    if not w3.is_connected():
        print("Error: Could not connect to Web3")
        return

    # Load Deployments
    DEPLOYMENTS_PATH = '/Users/nasibgojayev/Desktop/visual_programming/smart-contracts/artifacts-store/local-deployments.json'
    with open(DEPLOYMENTS_PATH, 'r') as f:
        deployments = json.load(f)
        
    registry_address = deployments.get('GrantRegistry')
    
    # Load ABI
    ABI_PATH = '/Users/nasibgojayev/Desktop/visual_programming/smart-contracts/artifacts/contracts/GrantRegistry.sol/GrantRegistry.json'
    with open(ABI_PATH, 'r') as f:
        abi = json.load(f)['abi']
        
    contract = w3.eth.contract(address=registry_address, abi=abi)
    
    # Debug Network
    chain_id = w3.eth.chain_id
    code = w3.eth.get_code(registry_address)
    print(f"Connected to Chain ID: {chain_id}")
    print(f"Code at {registry_address}: {code.hex()[:10]}... ({len(code)} bytes)")
    
    if len(code) <= 2: # 0x
        print("CRITICAL ERROR: No code at registry address! Contracts not deployed on this chain.")
        return

    # Send Transaction
    print("Creating Proposal on-chain...")
    account = w3.eth.accounts[0] # Hardhat #0
    
    tx_hash = contract.functions.createGrant(
        json.dumps({"title": "Test Proposal", "description": "Verified", "budget": 100})
    ).transact({'from': account})
    
    print(f"Transaction sent: {tx_hash.hex()}")
    print("Waiting for block...")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Mined.")
    
    # Check Events
    print("Checking for events...")
    logs = contract.events.GrantCreated().get_logs(fromBlock=0)
    print(f"Found {len(logs)} GrantCreated events on chain.")
    for log in logs:
        print(f" - {log['args']}")
    
    # Wait for indexer (poll DB)
    print("Waiting for indexer to sync...")
    for i in range(10):
        time.sleep(2)
        count = Proposal.objects.filter(title="Test Proposal").count()
        if count > 0:
            print("SUCCESS: Proposal found in DB!")
            return
        print(f"Checking DB... ({i+1}/10)")
        
    print("FAILURE: Proposal not found in DB after 20s.")

if __name__ == "__main__":
    run()

from django.core.management.base import BaseCommand
from base.management.commands.run_indexer import Command as IndexerCommand
from web3 import Web3
from django.conf import settings
import os
import json

class Command(IndexerCommand):
    help = 'Backfill events from a specific block range'

    def add_arguments(self, parser):
        parser.add_argument('--fromBlock', type=int, default=0)
        parser.add_argument('--toBlock', type=str, default='latest')

    def handle(self, *args, **options):
        HTTP_PROVIDER = "http://127.0.0.1:8545"
        w3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER))
        
        if not w3.is_connected():
             self.stdout.write(self.style.ERROR('Failed to connect to Web3'))
             return

        from_block = options['fromBlock']
        to_block_arg = options['toBlock']
        
        if to_block_arg == 'latest':
            to_block = w3.eth.block_number
        else:
            to_block = int(to_block_arg)

        # Re-use setup logic from IndexerCommand
        # (Copy-pasting for safety if inheritance is tricky with management commands, but inheritance generally works)
        # For simplicity, let's copy the setup since 'handle' is overridden
        
        BASE_DIR = settings.BASE_DIR
        ABI_DIR = os.path.join(BASE_DIR, 'doncoin/base/abis')
        contracts = {}
        contract_names = ['RoundManager', 'GrantRegistry', 'DonationVault', 'MatchingPool']
        DEPLOYMENTS_PATH = os.path.join(BASE_DIR, '../../smart-contracts/artifacts-store/local-deployments.json')
        
        if not os.path.exists(DEPLOYMENTS_PATH):
             self.stdout.write(self.style.ERROR(f'Deployments not found'))
             return

        with open(DEPLOYMENTS_PATH, 'r') as f:
            deployments = json.load(f)

        for name in contract_names:
            abi_path = os.path.join(ABI_DIR, f'{name}.json')
            if os.path.exists(abi_path) and name in deployments:
                with open(abi_path, 'r') as f:
                    abi = json.load(f)
                contracts[name] = w3.eth.contract(address=deployments[name], abi=abi)

        LOG_FILE = os.path.join(BASE_DIR, 'transactions.json')
        
        self.stdout.write(f'Backfilling from {from_block} to {to_block}...')
        
        # Process in chunks to avoid timeouts
        CHUNK_SIZE = 1000
        for start in range(from_block, to_block + 1, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE - 1, to_block)
            self.process_blocks(w3, contracts, start, end, LOG_FILE)
            
        self.stdout.write(self.style.SUCCESS('Backfill complete'))

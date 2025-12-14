import time
import json
import os
import datetime
import uuid
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from web3 import Web3
from decimal import Decimal
from base.models import ChainSession, ContractEvent, Round, MatchingPool, Proposal, Donor, Wallet, Donation
from base.utils.blockchain_logger import blockchain_logger

# Configure indexer logger
logger = logging.getLogger('indexer')
bc_logger = blockchain_logger

class Command(BaseCommand):
    help = 'Runs the event indexer for smart contracts'

    def handle(self, *args, **options):
        # Configuration
        # Configuration
        # Load env from workspace root (2 levels up)
        from dotenv import load_dotenv
        load_dotenv(settings.BASE_DIR.parent.parent / '.env')
        
        HTTP_PROVIDER = os.getenv('HARDHAT_RPC_URL', "http://127.0.0.1:8545") 
        POLL_INTERVAL = 2
        BASE_DIR = settings.BASE_DIR
        
        # Connect to Web3
        w3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER))
        if not w3.is_connected():
            logger.error('Failed to connect to Web3 provider at %s', HTTP_PROVIDER)
            self.stdout.write(self.style.ERROR('Failed to connect to Web3 provider'))
            return

        logger.info('Connected to Web3 provider at %s', HTTP_PROVIDER)
        self.stdout.write(self.style.SUCCESS('Connected to Web3 provider'))
        
        # Load ABIs
        # Correct path dynamically
        PROJECT_ROOT = settings.BASE_DIR.parent.parent
        ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'smart-contracts/artifacts/contracts')
        DEPLOYMENTS_PATH = os.path.join(PROJECT_ROOT, 'smart-contracts/artifacts-store/local-deployments.json')
        
        if not os.path.exists(DEPLOYMENTS_PATH):
             logger.error('Deployments file not found at %s', DEPLOYMENTS_PATH)
             self.stdout.write(self.style.ERROR(f'Deployments file not found at {DEPLOYMENTS_PATH}'))
             return

        with open(DEPLOYMENTS_PATH, 'r') as f:
            deployments = json.load(f)
        
        contracts = {}
        contract_names = ['RoundManager', 'GrantRegistry', 'DonationVault']
        
        for name in contract_names:
            # Hardhat structure: Contract.sol/Contract.json
            abi_path = os.path.join(ARTIFACTS_DIR, f'{name}.sol', f'{name}.json')
            if os.path.exists(abi_path) and name in deployments:
                with open(abi_path, 'r') as f:
                    data = json.load(f)
                    abi = data['abi'] # Hardhat artifacts wrap ABI in 'abi' key
                contracts[name] = w3.eth.contract(address=deployments[name], abi=abi)
                logger.info('Loaded contract %s at %s', name, deployments[name])
                self.stdout.write(f'Loaded contract {name} at {deployments[name]}')
            else:
                 logger.warning('Could not load %s from %s', name, abi_path)
                 self.stdout.write(self.style.WARNING(f'Could not load {name} from {abi_path}'))

        # Get or create chain session based on GrantRegistry address + deployment block hash
        grant_registry_address = deployments.get('GrantRegistry')
        if not grant_registry_address:
            self.stdout.write(self.style.ERROR('GrantRegistry address not found in deployments'))
            return
        
        # Find deployment block by checking when the contract code first appeared
        # We use the block HASH as identifier - it's unique per node session even if addresses/blocks are same
        deployment_block = 0
        deployment_block_hash = ''
        try:
            current_block = w3.eth.block_number
            # Check if code exists at current block (contract is deployed)
            code = w3.eth.get_code(grant_registry_address, block_identifier=current_block)
            if code and code != b'' and code != b'0x':
                # Binary search to find deployment block
                low, high = 0, current_block
                while low < high:
                    mid = (low + high) // 2
                    mid_code = w3.eth.get_code(grant_registry_address, block_identifier=mid)
                    if mid_code and mid_code != b'' and mid_code != b'0x':
                        high = mid
                    else:
                        low = mid + 1
                deployment_block = low
                
                # Get the block hash - this is UNIQUE per node session
                block_info = w3.eth.get_block(deployment_block)
                deployment_block_hash = block_info['hash'].hex()
                
                self.stdout.write(f'Detected GrantRegistry deployment at block {deployment_block}')
                self.stdout.write(f'Block hash: {deployment_block_hash[:16]}...')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not detect deployment block: {e}'))
        
        chain_session, session_created = ChainSession.get_or_create_for_deployment(
            grant_registry_address, deployment_block, deployment_block_hash
        )
        if session_created:
            self.stdout.write(self.style.SUCCESS(f'Created new chain session: {chain_session.session_id}'))
        else:
            self.stdout.write(f'Using existing chain session: {chain_session.session_id}')
        
        # Store session on self for use in handlers
        self.chain_session = chain_session

        # Main Loop
        # Start from block 0 to ensure we catch past events (Backfill)
        # In production, we would store the last processed block in DB.
        latest_block = 0 
        LOG_FILE = os.path.join(BASE_DIR, 'transactions.json')
        
        self.stdout.write(f'Starting indexer from block {latest_block}...')

        while True:
            try:
                current_block = w3.eth.block_number
                if current_block > latest_block:
                    self.process_blocks(w3, contracts, latest_block + 1, current_block, LOG_FILE)
                    latest_block = current_block
                time.sleep(POLL_INTERVAL)
            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS('Stopping indexer...'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                time.sleep(POLL_INTERVAL)

    def process_blocks(self, w3, contracts, start_block, end_block, log_file):
        start_time = time.time()
        logger.debug('Processing blocks %d to %d', start_block, end_block)
        self.stdout.write(f'Processing blocks {start_block} to {end_block}')
        
        # Interests: Contract -> [Events]
        interests = {
            'GrantRegistry': ['GrantCreated'],
            'DonationVault': ['DonationReceived'], 
        }

        for name, contract in contracts.items():
            if name not in interests: continue
            
            for event_name in interests[name]:
                try:
                    # Generic get_logs is safer than create_filter for historic data
                    event_cls = getattr(contract.events, event_name)
                    entries = event_cls().get_logs(fromBlock=start_block, toBlock=end_block)
                    
                    if entries:
                        logger.info('Found %d events for %s.%s', len(entries), name, event_name)
                        self.stdout.write(f"Found {len(entries)} events for {name}.{event_name}")

                    for event in entries:
                        self.handle_event(w3, event, name, event_name, log_file)
                except Exception as e:
                    logger.error('Error fetching logs for %s.%s: %s', name, event_name, str(e))
                    self.stdout.write(self.style.ERROR(f"Error fetching logs for {name}.{event_name}: {e}"))

    def handle_event(self, w3, event, contract_name, event_name, log_file):
        tx_hash = event['transactionHash'].hex()
        args = dict(event['args'])
        block_number = event['blockNumber']
        log_index = event['logIndex'] # Unique ID within block
        
        # Get timestamp from block
        block = w3.eth.get_block(block_number)
        timestamp_unix = block['timestamp']
        timestamp_dt = datetime.datetime.fromtimestamp(timestamp_unix, tz=datetime.timezone.utc)

        # Idempotency Check: include chain_session to allow same event across sessions
        if ContractEvent.objects.filter(
            tx_hash=tx_hash, 
            event_type=f"{contract_name}.{event_name}",
            chain_session=self.chain_session
        ).exists():
            return

        # Log using blockchain logger
        bc_logger.log_event(
            contract_name=contract_name,
            event_name=event_name,
            event_data=args,
            block_number=block_number,
            tx_hash=tx_hash
        )
        logger.info('New Event: %s.%s in %s at block %d', contract_name, event_name, tx_hash, block_number)
        self.stdout.write(self.style.SUCCESS(f'New Event: {event_name} in {tx_hash}'))

        # --- SYNC LOGIC ---

        if event_name == 'GrantCreated':
            # Event: GrantCreated(uint256 id, address owner, string metadata)
            grant_id = args.get('id')
            proposer_address = args.get('owner')
            metadata_str = args.get('metadata')
            
            try:
                metadata = json.loads(metadata_str)
            except:
                metadata = {'title': f"Grant {grant_id}", 'description': 'No metadata'}

            # Get/Create Donor
            wallet, _ = Wallet.objects.get_or_create(address=proposer_address)
            donor, _ = Donor.objects.get_or_create(wallet=wallet, defaults={'username': proposer_address})
            
            # Find active round
            active_round = Round.objects.filter(status='active').first()
            if not active_round:
                # Fallback
                mp, _ = MatchingPool.objects.get_or_create(pool_id=f"{uuid.uuid4()}", defaults={'total_funds': 0})
                active_round = Round.objects.create(
                    matching_pool=mp,
                    start_date=timezone.now(),
                    end_date=timezone.now() + datetime.timedelta(days=30),
                    status='active'
                )

            proposal, created = Proposal.objects.update_or_create(
                on_chain_id=grant_id,
                chain_session=self.chain_session,
                defaults={
                    'title': metadata.get('title', f'Grant {grant_id}'),
                    'description': metadata.get('description', ''),
                    'proposer': donor,
                    'round': active_round,
                    'funding_goal': Decimal(str(metadata.get('budget', 0))),
                    'status': 'pending'
                }
            )
            logger.info('Synced Proposal: %s (on-chain ID: %s)', proposal.title, grant_id)
            self.stdout.write(f"Synced Proposal: {proposal.title} (ID: {grant_id})")

        elif event_name == 'DonationReceived':
            # Event: DonationReceived(donor, token, amount, roundId, grantId)
            donor_address = args.get('donor')
            grant_id = args.get('grantId')
            amount_wei = args.get('amount')
            amount_eth = Decimal(amount_wei) / Decimal(10**18)
            
            # Get Donor
            wallet, _ = Wallet.objects.get_or_create(address=donor_address)
            donor, _ = Donor.objects.get_or_create(wallet=wallet, defaults={'username': donor_address})
            
            # Find Proposal by on_chain_id and chain_session
            try:
                proposal = Proposal.objects.get(on_chain_id=grant_id, chain_session=self.chain_session)
                
                Donation.objects.create(
                    donor=donor,
                    proposal=proposal,
                    amount=amount_eth,
                    description=f"On-chain donation to Grant {grant_id}"
                )
                # Update totals
                proposal.total_donations = Decimal(str(proposal.total_donations)) + amount_eth
                proposal.save()
                self.stdout.write(f"Synced Donation of {amount_eth} ETH to Proposal {proposal.proposal_id}")
            except Proposal.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Donation for unknown proposal ID {grant_id}"))

        # --- END SYNC LOGIC ---

        # Log Event
        ContractEvent.objects.create(
            chain_session=self.chain_session,
            event_type=f"{contract_name}.{event_name}",
            tx_hash=tx_hash,
            timestamp=timestamp_dt,
            proposal=proposal if 'proposal' in locals() else None,
            round=active_round if 'active_round' in locals() else None 
        )
        
        # Log to JSON
        log_entry = {
            "contract": contract_name,
            "event": event_name,
            "tx_hash": tx_hash,
            "block": block_number,
            "timestamp": str(timestamp_dt),
            "args": json.loads(json.dumps(args, default=str))
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from web3 import Web3
import json
import os

class ClaimTokensView(APIView):
    def post(self, request):
        wallet_address = request.data.get('wallet_address')
        if not wallet_address:
            return Response({"error": "wallet_address is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Config
        from dotenv import load_dotenv
        load_dotenv(settings.BASE_DIR.parent.parent / '.env')
        HTTP_PROVIDER = os.getenv('HARDHAT_RPC_URL', "http://127.0.0.1:8545")
        # Hardhat Account #0 Private Key (Publicly Known)
        PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        SENDER_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" # Account #0
        
        try:
            w3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER))
            if not w3.is_connected():
                return Response({"error": "Blockchain node not connected"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Load Contract
            # We assume contracts are at this path (same as indexer)
            PROJECT_ROOT = settings.BASE_DIR.parent.parent
            DEPLOYMENTS_PATH = os.path.join(PROJECT_ROOT, 'smart-contracts/artifacts-store/local-deployments.json')
            if not os.path.exists(DEPLOYMENTS_PATH):
                 return Response({"error": "Deployments file not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            with open(DEPLOYMENTS_PATH, 'r') as f:
                deployments = json.load(f)
            
            gov_token_address = deployments.get('GovernanceToken')
            if not gov_token_address:
                return Response({"error": "GovernanceToken address not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Minimal ABI for transfer
            min_abi = [
                {
                    "constant": False,
                    "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                    "name": "transfer",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ]
            
            contract = w3.eth.contract(address=gov_token_address, abi=min_abi)
            
            # Prepare Transaction
            amount = w3.to_wei(1000, 'ether')
            nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)
            
            tx = contract.functions.transfer(wallet_address, amount).build_transaction({
                'chainId': 31337, # Hardhat Default
                'gas': 200000,
                'gasPrice': w3.to_wei('1', 'gwei'),
                'nonce': nonce,
            })
            
            # Sign & Send
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            # Correct attribute is rawTransaction (camelCase in some versions, but check dir if unsure. Standard is rawTransaction)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return Response({
                "message": "Tokens sent successfully!",
                "tx_hash": w3.to_hex(tx_hash),
                "amount": "1000 GOV"
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

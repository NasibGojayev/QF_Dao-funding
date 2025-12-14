from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from base.models import Wallet, Donor
from api.serializers import DonorSerializer
from eth_account.messages import encode_defunct
from eth_account import Account
import uuid

from rest_framework.permissions import AllowAny

class WalletLoginView(APIView):
    """
    Login with Ethereum Wallet.
    Expects: { "address": "0x...", "signature": "0x...", "message": "Login with..." }
    """
    authentication_classes = [] # Disable CSRF usage via SessionAuth
    permission_classes = [AllowAny]
    
    def post(self, request):
        address = request.data.get('address')
        signature = request.data.get('signature')
        message = request.data.get('message')
        
        if not address or not signature or not message:
            return Response({'error': 'Missing credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Verify Signature
        try:
            # Reconstruct the message object
            msg_obj = encode_defunct(text=message)
            
            # Recover address from signature
            recovered_address = Account.recover_message(msg_obj, signature=signature)
            
            if recovered_address.lower() != address.lower():
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            return Response({'error': f'Verification failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Login Successful - strict sync with DB
        
        # Get or Create Wallet
        wallet, _ = Wallet.objects.get_or_create(address=address)
        
        # Get or Create Donor (The User Model)
        # We explicitly set username to address to ensure uniqueness if creating
        donor, created = Donor.objects.get_or_create(
            wallet=wallet,
            defaults={'username': address} 
        )
        
        # If username is missing (for some reason), update it
        if not donor.username:
            donor.username = address
            donor.save()

        # Update last login or similar logic if needed (AbstractBaseUser has last_login)
        donor.last_login =  __import__('django.utils.timezone').utils.timezone.now()
        donor.save()
            
        return Response({
            'message': 'Login successful',
            'user': DonorSerializer(donor).data, # Replaces 'user' and 'donor' keys with single object
            'wallet_address': address
        })

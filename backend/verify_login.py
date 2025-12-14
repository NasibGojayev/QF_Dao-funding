import requests
import json
from eth_account import Account
from eth_account.messages import encode_defunct

# Setup
API_URL = "http://127.0.0.1:8000/auth/wallet/"
# Create a fresh wallet
wallet = Account.create()
address = wallet.address
private_key = wallet.key

print(f"Testing Login for address: {address}")

# 1. Prepare Message and Signature
message_text = f"Login to DonCoin with address: {address}"
message_hash = encode_defunct(text=message_text)
signature = wallet.sign_message(message_hash).signature.hex()

# 2. Payload
payload = {
    "address": address,
    "signature": signature,
    "message": message_text
}

# 3. Send Request
try:
    response = requests.post(API_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")

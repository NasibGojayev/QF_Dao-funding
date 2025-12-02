import json
import os
from web3 import Web3

# Get the directory of this file and construct path to artifacts
current_dir = os.path.dirname(os.path.abspath(__file__))
artifact_path = os.path.join(current_dir, "..", "artifacts", "contracts", "GrantRegistry.sol", "GrantRegistry.json")

# Load contract ABI
try:
    with open(artifact_path) as f:
        contract_data = json.load(f)
        GRANT_REGISTRY_ABI = contract_data["abi"]
except FileNotFoundError:
    raise FileNotFoundError(
        f"Contract artifact not found at {artifact_path}. "
        "Please compile the contracts first using: npx hardhat compile"
    )

# Contract address (update this after deployment)
# Using checksum address as required by web3.py
GRANT_REGISTRY_ADDRESS = Web3.to_checksum_address("0xfbab4aa40c202e4e80390171e82379824f7372dd")


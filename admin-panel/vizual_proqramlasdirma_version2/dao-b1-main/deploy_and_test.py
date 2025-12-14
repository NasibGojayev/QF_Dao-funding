#!/usr/bin/env python
"""
Deploy contract to in-process network and generate sample transactions.
"""
import subprocess
import json
import os

hardhat_local = r"c:\Users\Qurban\OneDrive\Desktop\dao-b1-main\dao-b1-main\hardhat_local"
project_root = r"c:\Users\Qurban\OneDrive\Desktop\dao-b1-main\dao-b1-main"

os.chdir(hardhat_local)

print("\n=== Deploying contract to in-process network ===")
result = subprocess.run(
    ["npx", "hardhat", "run", "scripts/deploy.js"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print("Deploy failed!")
    print(result.stderr)
    exit(1)

# Extract address from output
lines = result.stdout.split('\n')
contract_address = None
for line in lines:
    if "deployed to:" in line:
        parts = line.split("deployed to:")
        contract_address = parts[1].strip()
        break

if not contract_address:
    print("Could not extract contract address!")
    exit(1)

print(f"\nContract deployed to: {contract_address}")

# Run Hardhat tests to generate events
print("\n=== Running Hardhat tests to generate events ===")
result = subprocess.run(
    ["npx", "hardhat", "test"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print("Tests failed!")
    print(result.stderr)

# Return address for indexer
print(f"\n{contract_address}")

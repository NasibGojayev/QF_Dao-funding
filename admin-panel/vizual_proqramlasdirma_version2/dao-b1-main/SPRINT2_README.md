# Sprint 2 — Database & Smart Contract

Quick start (local):

1) Install Python deps (prefer venv):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements-sprint2.txt
```

2) Create DB & seed sample data:

```powershell
python backend\seed_db.py
```

3) Run Alembic migrations (local):

```powershell
# from backend folder
alembic -c alembic.ini upgrade head
```

4) Run Hardhat tests locally (requires Node):

```powershell
npm install
npx hardhat test
```

5) Compile and deploy to local hardhat node:

```powershell
npx hardhat node
npm run deploy:local
```

6) Run indexer (local):

```powershell
python indexer\indexer.py --rpc http://127.0.0.1:8545 --contract-address 0x... --abi artifacts\MilestoneFunding.abi.json
```

Notes:
- For testnet deployment (Sepolia) set `SEPOLIA_RPC_URL` and `DEPLOYER_PRIVATE_KEY` in `.env` and run `npm run deploy:sepolia`.
- The indexer/backfill scripts expect a compiled ABI under `artifacts/`.

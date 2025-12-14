# DonCoin Project

## How to Run (The Easy Way - Docker)

Perfect for running the entire stack in one go.

### Prerequisites
- Docker & Docker Compose

### 1. Start Everything
Run this command in the root folder:
```bash
docker compose up
```

### What happens automatically?
1.  **Blockhain Starts**: A local Hardhat node spins up.
2.  **Contracts Deploy**: A temporary `deployer` container runs `deploy.js` to deploy contracts to the node.
3.  **Services Start**: The Backend and Frontend wait for deployment to finish, then start.

**Access the App:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Blockchain: http://localhost:8545

### 2. Stop Everything
```bash
docker compose down
```

---

## Manual Setup (If not using Docker)

### 1. Start the Local Blockchain Node
```bash
cd smart-contracts
npx hardhat node
```

### 2. Deploy Smart Contracts (CRITICAL)
**Run this every time you restart the node.**
```bash
cd smart-contracts
npx hardhat run scripts/deploy.js --network localhost
```

### 3. Start Backend Services
**Indexer:**
```bash
cd backend/doncoin
python manage.py run_indexer
```
**API:**
```bash
cd backend/doncoin
python manage.py runserver
```

### 4. Start Frontend
```bash
cd my-app
npm run dev
```

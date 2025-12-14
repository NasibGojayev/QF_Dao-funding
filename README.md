# 🏛️ QF DAO Funding - Quadratic Funding Decentralized Autonomous Organization

A full-stack decentralized application for **quadratic funding** governance. Create and manage grant proposals, vote on funding decisions, and participate in DAO governance using blockchain technology.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Manual Setup](#-manual-setup)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

- **Smart Contract Governance** - Solidity contracts for proposal creation, voting, and fund distribution
- **Quadratic Funding Algorithm** - Fair matching pool distribution based on community contributions
- **Web3 Wallet Integration** - Connect with MetaMask and other wallets via RainbowKit
- **Real-time Blockchain Indexer** - Django-based ETL that syncs on-chain events to database
- **Modern Frontend** - Next.js 16 with React 19 and TailwindCSS
- **REST API** - Django REST Framework backend for off-chain data

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Blockchain** | Hardhat, Solidity, OpenZeppelin |
| **Frontend** | Next.js 16, React 19, TailwindCSS, wagmi, viem |
| **Backend** | Django 5, Django REST Framework, PostgreSQL |
| **Indexer** | Python, web3.py, Django Management Commands |

---

## 📦 Prerequisites

Before running this project, ensure you have:

- **Node.js** v18+ and **npm** v9+
- **Python** 3.10+
- **PostgreSQL** (or use SQLite for development)
- **Git**

---

## 🚀 Quick Start

### Option 1: Automated Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/NasibGojayev/QF_Dao-funding.git
cd QF_Dao-funding

# Make the setup script executable
chmod +x setup.sh

# Run the setup (installs dependencies and starts all services)
./setup.sh
```

### Option 2: Using start-all.sh (After Initial Setup)

If dependencies are already installed:
```bash
./start-all.sh
```

---

## 🔧 Manual Setup

If you prefer to set up each component manually, follow these steps:

### Step 1: Clone & Configure Environment

```bash
git clone https://github.com/NasibGojayev/QF_Dao-funding.git
cd QF_Dao-funding

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Step 2: Smart Contracts Setup

```bash
cd smart-contracts

# Install dependencies
npm install

# Start local Hardhat node (keep this terminal running!)
npx hardhat node
```

**In a NEW terminal:**
```bash
cd smart-contracts

# Deploy contracts to local network
npx hardhat run scripts/deploy.js --network localhost
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd doncoin
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the Django server (keep this terminal running!)
python manage.py runserver
```

### Step 4: Start the Indexer

**In a NEW terminal:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd doncoin

# Start blockchain indexer (keep this terminal running!)
python manage.py run_indexer
```

### Step 5: Frontend Setup

**In a NEW terminal:**
```bash
cd my-app

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 6: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Hardhat RPC**: http://localhost:8545

---

## 📁 Project Structure

```
QF_Dao-funding/
├── smart-contracts/       # Solidity contracts & Hardhat config
│   ├── contracts/         # Smart contract source files
│   ├── scripts/           # Deployment scripts
│   └── test/              # Contract tests
│
├── backend/               # Django backend
│   └── doncoin/           # Main Django project
│       ├── base/          # Core app with models, views, indexer
│       └── manage.py
│
├── my-app/                # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   └── lib/               # Utilities & config
│
├── admin-panel-ui/        # Admin dashboard (optional)
├── data-science/          # Analytics & ML models
├── security/              # Security monitoring tools
│
├── setup.sh               # One-click setup script
├── start-all.sh           # Start all services script
├── docker-compose.yml     # Docker orchestration
└── README.md              # This file
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
# Host Configuration
HOST_IP=127.0.0.1

# Ports
HARDHAT_PORT=8545
DJANGO_PORT=8000
NEXT_PORT=3000

# URLs (auto-generated from above)
HARDHAT_RPC_URL=http://127.0.0.1:8545
DJANGO_API_URL=http://127.0.0.1:8000

# Database (PostgreSQL)
DB_NAME=doncoin
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Or use SQLite (default for development)
# DATABASE_URL=sqlite:///db.sqlite3
```

---

## 🐛 Troubleshooting

### Proposals not showing up?

**Cause**: The Hardhat node was restarted but contracts weren't redeployed.

**Solution**: Always redeploy contracts after restarting the Hardhat node:
```bash
cd smart-contracts
npx hardhat run scripts/deploy.js --network localhost
```

### Backend can't connect to database?

**Solution**: Check your database credentials in `.env` and ensure PostgreSQL is running:
```bash
# Start PostgreSQL (macOS)
brew services start postgresql

# Or use SQLite by updating settings.py
```

### Frontend wallet connection issues?

**Solution**: Ensure you're using a fresh MetaMask account or reset your account:
1. Open MetaMask → Settings → Advanced → Reset Account
2. Re-import a Hardhat test account (private keys shown when running `npx hardhat node`)

### Port already in use?

**Solution**: Kill the process using the port:
```bash
# Find and kill process on port 3000
lsof -i :3000
kill -9 <PID>

# Or use different ports in .env
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 👥 Contributors

- **Nasib Gojayev** - [GitHub](https://github.com/NasibGojayev)

---

Made with ❤️ for the blockchain community

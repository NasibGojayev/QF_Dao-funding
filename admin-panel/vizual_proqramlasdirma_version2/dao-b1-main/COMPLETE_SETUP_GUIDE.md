# Quadratic Funding DAO - Complete Setup Guide

A full-stack Web3 platform for quadratic funding, built with Next.js, Django, FastAPI, and Solidity smart contracts.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)
- Git

### 1. Clone & Navigate
```bash
cd dao-b1-main
```

### 2. Start All Services (Parallel Terminals)

**Terminal 1: Frontend**
```powershell
cd frontend_next
npm install  # if not done
npm run dev
# Opens on http://localhost:3000
```

**Terminal 2: Django Backend**
```powershell
cd backend
python -m venv .venv  # one-time
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # one-time
python manage.py migrate  # one-time
python manage.py runserver
# Runs on http://localhost:8000
```

**Terminal 3: FastAPI Microservice**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn fastapi_service.main:app --port 8001 --reload
# Runs on http://localhost:8001
```

**Terminal 4: Smart Contracts (Optional)**
```powershell
cd contracts
npm install  # one-time
npx hardhat compile
npx hardhat node
# Local blockchain on http://localhost:8545
```

---

## 📖 Documentation

### Frontend (`frontend_next/`)
- **Framework:** Next.js 14 with App Router
- **Styling:** Tailwind CSS
- **Web3:** wagmi + viem
- **Key Pages:**
  - `/` - Home with hero section
  - `/projects` - Project listings
  - `/rounds` - Funding rounds
  - `/submit` - Submit proposals
  - `/governance` - DAO governance
  - `/admin` - Admin dashboard

**Start:** `npm run dev` in `frontend_next/`

### Backend (`backend/`)

#### Django REST API
- **Port:** 8000
- **Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api/

**Endpoints:**
```
GET    /                         # API info
POST   /api-token-auth/         # Get auth token
GET    /api/projects/           # List projects
POST   /api/projects/           # Create project
GET    /api/projects/{id}/      # Get details
PUT    /api/projects/{id}/      # Update project
DELETE /api/projects/{id}/      # Delete project
```

**Start:** `python manage.py runserver`

#### FastAPI Microservice
- **Port:** 8001
- **Docs:** http://localhost:8001/docs
- **GraphQL:** http://localhost:8001/graphql

**Endpoints:**
```
GET    /api/history              # Transaction history
GET    /api/tx/{hash}           # TX details
POST   /admin/resolve           # Admin actions
GET    /graphql                 # GraphQL endpoint
WS     /ws/events               # WebSocket events
POST   /json-rpc                # JSON-RPC endpoint
```

**Start:** `uvicorn fastapi_service.main:app --reload --port 8001`

### Smart Contracts (`contracts/`)
- **Framework:** Hardhat + Solidity 0.8.19
- **Chain Library:** OpenZeppelin

**Contracts:**
1. `GovernanceToken.sol` - ERC20 governance token
2. `GrantRegistry.sol` - Project registry
3. `DonationVault.sol` - Donation tracking
4. `MatchingPool.sol` - Matching pool logic

**Compile:** `npx hardhat compile`  
**Deploy:** `npx hardhat run scripts/deploy.js --network localhost`

---

## 🔐 Authentication & Security

### API Authentication
1. Create a user in Django admin (http://localhost:8000/admin)
2. Get token:
   ```powershell
   $response = Invoke-RestMethod -Uri "http://localhost:8000/api-token-auth/" `
     -Method Post `
     -Body @{ username = "admin"; password = "password" } | ConvertTo-Json
   ```
3. Use in API calls:
   ```powershell
   $headers = @{ Authorization = "Token YOUR_TOKEN" }
   Invoke-RestMethod -Uri "http://localhost:8000/api/projects/" -Headers $headers
   ```

### Web3 Security
- MetaMask/WalletConnect integration
- Smart contract audited libraries (OpenZeppelin)
- Rate limiting on API endpoints

---

## 📁 Project Structure

```
dao-b1-main/
├── frontend_next/              # Next.js frontend (PRIMARY)
│   ├── app/                    # 16 routes
│   │   ├── page.tsx           # Home
│   │   ├── projects/          # Projects page
│   │   ├── rounds/            # Rounds page
│   │   ├── submit/            # Submit proposal
│   │   ├── governance/        # Governance
│   │   ├── admin/             # Admin panel
│   │   ├── token/             # Token management
│   │   ├── vault/             # Donation vault
│   │   ├── wallet/            # Wallet connect
│   │   ├── security/          # Security info
│   │   └── terms/             # Terms & privacy
│   ├── components/            # 20+ reusable components
│   ├── providers/             # Web3Provider
│   ├── styles/                # Tailwind + globals
│   ├── utils/                 # Helper functions
│   ├── next.config.ts         # Next.js config
│   ├── tailwind.config.ts     # Tailwind config
│   └── package.json           # Dependencies
│
├── frontend/                   # Vite + React (secondary)
│   ├── src/components/        # React components
│   ├── src/contracts/         # Contract ABIs
│   ├── src/hooks/            # Web3 hooks
│   ├── src/pages/            # Page views
│   └── vite.config.ts        # Vite config
│
├── backend/                    # Django + FastAPI
│   ├── api/                   # Django app
│   │   ├── models.py          # Project, Round, Grant
│   │   ├── serializers.py     # DRF serializers
│   │   ├── views.py           # Viewsets
│   │   └── urls.py            # Routing
│   ├── fastapi_service/       # FastAPI app
│   │   └── main.py            # Full microservice
│   ├── backend_project/       # Django settings
│   │   ├── settings.py        # Django config
│   │   ├── urls.py            # Root routing
│   │   └── wsgi.py            # WSGI config
│   ├── manage.py              # Django CLI
│   ├── requirements.txt       # Python packages
│   └── db.sqlite3             # Dev database
│
├── contracts/                  # Solidity + Hardhat
│   ├── contracts/
│   │   ├── GovernanceToken.sol
│   │   ├── GrantRegistry.sol
│   │   ├── DonationVault.sol
│   │   └── MatchingPool.sol
│   ├── scripts/
│   │   └── deploy.js          # Deployment script
│   ├── hardhat.config.js      # Hardhat config
│   ├── artifacts/             # Compiled ABIs
│   ├── package.json           # npm packages
│   └── deployed-addresses.json # (generated on deploy)
│
├── docs/                       # Documentation
│   ├── design_docs.md         # System design
│   └── system_description.md  # Description
│
├── PROJECT_STATUS.md          # This document
└── README.md                  # Quick reference
```

---

## 🛠️ Development Tips

### Hot Reload
- **Frontend:** Next.js automatically reloads on file changes
- **Backend:** FastAPI `--reload` flag enables hot reload
- **Django:** `runserver` auto-reloads on Python changes

### Database
- Default: SQLite (`db.sqlite3`)
- To reset: Delete `db.sqlite3`, run `python manage.py migrate`
- To create new migration: `python manage.py makemigrations api`

### Contract Development
- Edit `.sol` files in `contracts/contracts/`
- Run `npx hardhat compile` after changes
- ABIs auto-extract to `frontend_next/src/contracts/abis.ts`

### Testing
```powershell
# Frontend
cd frontend_next
npm run build  # Build test

# Backend
cd backend
python -m pytest  # (if pytest installed)

# Contracts
cd contracts
npx hardhat test  # (if tests written)
```

---

## 🚢 Deployment

### Frontend
```powershell
cd frontend_next
npm run build      # Creates .next/ folder
npm run start      # Production server
```

### Backend
```powershell
# Use a production WSGI server (Gunicorn, Waitress, etc.)
pip install gunicorn
gunicorn backend_project.wsgi:application --bind 0.0.0.0:8000
```

### Contracts
```powershell
# Deploy to testnet (e.g., Sepolia)
npx hardhat run scripts/deploy.js --network sepolia
```

---

## 🐛 Troubleshooting

### Port Already in Use
```powershell
# Find and kill process on port
Get-Process | Where-Object {$_.Port -eq 3000} | Stop-Process
# Or use different port: npm run dev -- -p 3001
```

### Module Not Found
```powershell
# Reinstall dependencies
npm install  # for frontend
pip install -r requirements.txt  # for backend
```

### Wallet Connection Issues
- Ensure MetaMask is installed and on the same network
- Check `.env.local` for `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`
- Web3Provider is set to fallback for missing projectId

### API Authorization Failed
- Create token: POST `/api-token-auth/` with credentials
- Include header: `Authorization: Token YOUR_TOKEN`
- Check token hasn't expired

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (localhost:3000)            │
│         Next.js 14 + React 19 + Tailwind CSS                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Navbar | Hero | Projects | Rounds | Governance     │   │
│  │ (Web3 Wallet Integration via wagmi + viem)         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Django API      │ │  FastAPI         │ │  Smart Contracts │
│  (8000)          │ │  (8001)          │ │  (8545)          │
│                  │ │                  │ │                  │
│ • REST APIs      │ │ • GraphQL        │ │ • ERC20 Token    │
│ • Token Auth     │ │ • WebSocket      │ │ • Project Reg.   │
│ • Projects/      │ │ • JSON-RPC       │ │ • Donation Vault │
│   Rounds/Grants  │ │ • Rate Limiting  │ │ • Matching Pool  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
        │                   │
        └───────────────────┴───────────────────┐
                                                │
                        ┌───────────────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  SQLite DB   │
                 │ (db.sqlite3) │
                 └──────────────┘
```

---

## 📞 Support & Documentation

- **Frontend Docs:** See `frontend_next/README.md`
- **Backend Docs:** See `backend/README.md`
- **Contracts Docs:** See `contracts/README.md`
- **Design Docs:** See `docs/design_docs.md`

---

## 📝 License

All code in this project is provided for educational and development purposes.

---

**Last Updated:** December 8, 2025  
**Status:** ✅ All Systems Operational

# DAO Quadratic Funding Platform - Complete Deployment Guide

## Prerequisites

- Docker & Docker Compose installed
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for production)
- Git

---

## Quick Start with Docker

### 1. Clone and Configure

```bash
git clone <repository-url>
cd dao-b1-main

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Django backend (port 8000)
- FastAPI microservice (port 8001)
- Next.js frontend (port 3000)
- Hardhat blockchain (port 8545)

### 3. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8001/docs
- **GraphQL:** http://localhost:8001/graphql

---

## Local Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Django
python manage.py runserver 0.0.0.0:8000

# In another terminal, start FastAPI
uvicorn fastapi_service.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
cd frontend_next

# Install dependencies
npm install

# Start development server
npm run dev
```

### Smart Contracts Setup

```bash
cd contracts

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Start local blockchain
npx hardhat node

# In another terminal, deploy contracts
npx hardhat run scripts/deploy.js --network localhost
```

---

## Production Deployment

### 1. Environment Configuration

Create `.env` file with production values:

```bash
# Django
DJANGO_SECRET_KEY=<generate-strong-secret>
DJANGO_DEBUG=0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/dao_db

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Blockchain
RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
PRIVATE_KEY=<deployment-private-key>
```

### 2. Database Setup

```bash
# Create database
createdb dao_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### 3. Deploy Smart Contracts

```bash
cd contracts

# Deploy to testnet (e.g., Sepolia)
npx hardhat run scripts/deploy.js --network sepolia

# Save contract addresses
# Update frontend .env with contract addresses
```

### 4. Build Frontend

```bash
cd frontend_next

# Build for production
npm run build

# Start production server
npm start
```

### 5. Start Backend Services

```bash
# Using gunicorn for Django
gunicorn backend_project.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Using uvicorn for FastAPI
uvicorn fastapi_service.main:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Docker Production Deployment

### 1. Build Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### 2. Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Run Migrations

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

---

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # FastAPI
    location /fastapi/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Monitoring & Logging

### Application Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Local logs
tail -f backend/logs/django.log
tail -f backend/logs/fastapi.log
```

### Metrics Dashboard

Access monitoring dashboard:
```bash
python backend/dashboard.py
# Visit http://localhost:8002
```

---

## Backup & Restore

### Database Backup

```bash
# Backup
pg_dump dao_db > backup_$(date +%Y%m%d).sql

# Restore
psql dao_db < backup_20251208.sql
```

### Contract Artifacts Backup

```bash
# Backup compiled contracts
tar -czf contracts_backup.tar.gz contracts/artifacts/
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Issues

```bash
# Check PostgreSQL status
systemctl status postgresql

# Restart PostgreSQL
systemctl restart postgresql
```

### Contract Deployment Fails

```bash
# Check network connection
npx hardhat run scripts/deploy.js --network localhost --verbose

# Verify account has funds
npx hardhat run scripts/check-balance.js
```

---

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=0 in production
- [ ] Use HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set secure cookie flags
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity

---

## Performance Optimization

### Database

```sql
-- Add indexes
CREATE INDEX idx_projects_created ON api_project(created_at);
CREATE INDEX idx_grants_project ON api_grant(project_id);
```

### Caching

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Frontend

```bash
# Enable Next.js caching
npm run build
# Serve with CDN
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
  
  frontend:
    deploy:
      replicas: 2
```

### Load Balancer

Use Nginx or HAProxy to distribute traffic across multiple instances.

---

*Last updated: December 8, 2025*

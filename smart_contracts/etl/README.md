# ETL Bridge for GrantRegistry Smart Contract

This ETL (Extract, Transform, Load) bridge connects the GrantRegistry smart contract on the blockchain to a backend database, enabling efficient querying and analysis of on-chain events.

## Overview

The ETL bridge monitors the `ProposalCreated` events emitted by the GrantRegistry contract and stores them in a database. It supports two modes:

- **Backfill Mode**: Extract historical events from past blocks
- **Listener Mode**: Monitor and capture new events in real-time

## Architecture

```
┌─────────────────┐
│  Smart Contract │
│  (GrantRegistry)│
└────────┬────────┘
         │ emits ProposalCreated events
         ▼
┌─────────────────┐
│   Extractor     │ ← Fetches events from blockchain
└────────┬────────┘
         ▼
┌─────────────────┐
│  Transformer    │ ← Maps event data to database schema
└────────┬────────┘
         ▼
┌─────────────────┐
│     Loader      │ ← Saves to database
└────────┬────────┘
         ▼
┌─────────────────┐
│    Database     │
│  (SQLite/Postgres)│
└─────────────────┘
```

## Database Schema

The `proposal_events` table stores the following fields:

| Column        | Type    | Description                           |
|---------------|---------|---------------------------------------|
| id            | Integer | Primary key (auto-increment)          |
| tx_hash       | String  | Transaction hash (unique)             |
| block_number  | BigInt  | Block number where event occurred     |
| proposal_id   | BigInt  | Proposal ID from the contract         |
| owner         | String  | Address of the proposal owner         |
| metadata_uri  | String  | URI to proposal metadata              |
| active        | Integer | Proposal status (1=active, 0=inactive)|

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Compile Smart Contracts

Make sure the GrantRegistry contract is compiled:

```bash
cd ..
npx hardhat compile
```

### 3. Deploy Contract (if needed)

Deploy the GrantRegistry contract and update the address in `contracts.py`:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

### 4. Configure Environment (Optional)

You can customize the configuration using environment variables:

```bash
export ETH_NODE_URL="http://127.0.0.1:8545"
export DATABASE_URL="sqlite:///etl_data.db"
export ETL_BATCH_SIZE="1000"
export ETL_POLL_INTERVAL="2"
```

## Usage

### Backfill Historical Events

Extract all historical events from the blockchain:

```bash
python run_etl.py backfill
```

With custom parameters:

```bash
python run_etl.py backfill --start-block 0 --end-block 1000 --batch-size 500
```

### Listen for New Events

Monitor the blockchain for new events in real-time:

```bash
python run_etl.py listener
```

With custom poll interval:

```bash
python run_etl.py listener --poll-interval 5
```

## Command-Line Arguments

### Backfill Mode

- `--start-block`: Starting block number (default: 0)
- `--end-block`: Ending block number (default: latest block)
- `--batch-size`: Number of blocks to process per batch (default: 1000)

### Listener Mode

- `--poll-interval`: Seconds between polling for new events (default: 2)

## How It Works

### 1. Extractor (`extractor.py`)

Connects to the Ethereum node and fetches event logs:
- `get_contract_events()`: Retrieves historical events for a block range
- `create_event_filter()`: Creates a filter for listening to new events

### 2. Transformer (`transformer.py`)

Maps raw event data to database schema:
- Extracts relevant fields from the event logs
- Converts data types as needed
- Structures data for database insertion

### 3. Loader (`loader.py`)

Saves transformed data to the database:
- Checks for duplicate events (by transaction hash)
- Handles database transactions with proper error handling
- Supports both single and batch inserts

### 4. Orchestration

- **Backfill** (`backfill.py`): Processes historical events in batches
- **Listener** (`listener.py`): Continuously polls for new events

## Database Options

### SQLite (Default)

Good for local development and testing:

```bash
export DATABASE_URL="sqlite:///etl_data.db"
```

### PostgreSQL

Recommended for production:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

## Logging

The ETL bridge includes comprehensive logging:
- INFO level: Normal operations, event counts, progress
- ERROR level: Failures, connection issues
- DEBUG level: Detailed event information

Logs are output to stdout with timestamps.

## Error Handling

The bridge includes robust error handling:
- Database connection failures
- Missing contract artifacts
- Blockchain connection issues
- Duplicate event detection
- Transaction rollback on errors

## Example Workflow

1. **Start Hardhat Node**:
   ```bash
   npx hardhat node
   ```

2. **Deploy Contract**:
   ```bash
   npx hardhat run scripts/deploy.js --network localhost
   ```

3. **Update Contract Address** in `contracts.py`

4. **Run Backfill**:
   ```bash
   python run_etl.py backfill
   ```

5. **Start Listener** (in another terminal):
   ```bash
   python run_etl.py listener
   ```

6. **Create Proposals** via contract interaction and watch them appear in the database!

## Troubleshooting

### "Contract artifact not found"

Make sure you've compiled the contracts:
```bash
cd .. && npx hardhat compile
```

### "Failed to connect to Ethereum node"

Ensure your Hardhat node is running:
```bash
npx hardhat node
```

### Database errors

Check your DATABASE_URL is correct and the database is accessible.

## Files

- `run_etl.py`: Main entry point with CLI
- `config.py`: Configuration and environment variables
- `contracts.py`: Contract ABI and address
- `db.py`: Database models and connection
- `extractor.py`: Blockchain event extraction
- `transformer.py`: Event data transformation
- `loader.py`: Database loading
- `backfill.py`: Historical event processing
- `listener.py`: Real-time event monitoring
- `logger.py`: Logging configuration

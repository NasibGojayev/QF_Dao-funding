import os

# Ethereum node configuration
NODE_URL = os.getenv("ETH_NODE_URL", "http://127.0.0.1:8545")

# Database configuration
# Default to SQLite for local development, can override with environment variable
DB_URL = os.getenv("DATABASE_URL", "sqlite:///etl_data.db")

# ETL configuration
BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "1000"))
POLL_INTERVAL = int(os.getenv("ETL_POLL_INTERVAL", "2"))  # seconds


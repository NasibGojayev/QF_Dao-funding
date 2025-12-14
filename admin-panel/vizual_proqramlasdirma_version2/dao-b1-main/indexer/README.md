# Indexer & Backfill

Usage examples:

1) Run the listener (local hardhat):

```powershell
python indexer\indexer.py --rpc http://127.0.0.1:8545 --contract-address 0xYourContract --abi ./artifacts/contracts/MilestoneFunding.sol/MilestoneFunding.json
```

2) Backfill historical logs:

```powershell
python indexer\backfill.py --rpc http://127.0.0.1:8545 --contract 0xYourContract --abi ./artifacts/contracts/MilestoneFunding.sol/MilestoneFunding.json --from 0 --to latest
```

Notes:
- The indexer uses `web3.py` and SQLAlchemy to persist events.
- Ensure `DATABASE_URL` env var is set or local sqlite `db.sqlite3` will be used.

Metrics & Monitoring:

- Both the indexer listener and the backfill worker expose Prometheus metrics on port `8003` by default.
- Metrics available:
	- `indexer_events_processed_total`
	- `indexer_events_duplicate_total`
	- `indexer_events_errors_total`
	- `indexer_event_process_duration_seconds`
	- `indexer_last_processed_block`
	- `backfill_events_persisted_total`
	- `backfill_events_duplicate_total`
	- `backfill_errors_total`
	- `backfill_duration_seconds`

Access metrics:

```powershell
curl http://127.0.0.1:8003/
```

Prometheus & Grafana example:

- Example Prometheus config (see `monitoring/prometheus.yml`) will scrape `localhost:8003`.
- To run Prometheus locally, download Prometheus and use this config file, then start Prometheus.

Grafana:

- Import `monitoring/grafana/indexer_dashboard.json` into Grafana (Dashboards -> Manage -> Import).
- Configure a Prometheus datasource pointing to your Prometheus server, then the dashboard panels will show indexer/backfill metrics.



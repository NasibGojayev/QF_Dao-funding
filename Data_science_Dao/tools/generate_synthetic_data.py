"""Generate ML synthetic data (raw_transactions.csv, features.csv, train_features.csv)

Usage:
    python -m doncoin.data_science.tools.generate_synthetic_data --out data/ --n 500
"""
import argparse
import os
from doncoin.data_science.pipelines.etl import ETLPipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="doncoin/data_science/data", help="output dir")
    parser.add_argument("--n", type=int, default=500, help="number of transactions to generate")
    args = parser.parse_args()
    out = os.path.abspath(args.out)
    p = ETLPipeline(out)
    raw_path, rows = p.generate_raw_transactions(n_transactions=args.n)
    feat_path, feats = p.transform_to_features(rows)
    print(f"Wrote raw: {raw_path}")
    print(f"Wrote features: {feat_path}")

if __name__ == '__main__':
    main()

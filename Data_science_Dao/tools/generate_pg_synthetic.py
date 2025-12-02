"""Generate PostgreSQL-style CSV files matching the project's schema.

Usage:
    python -m doncoin.data_science.tools.generate_pg_synthetic --out doncoin/data_science/data_pg --counts 200
"""
import argparse
import os
import csv
import uuid
import random
import datetime

def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def gen_base_wallet(n):
    rows = []
    for _ in range(n):
        rows.append({
            "id": str(uuid.uuid4()),
            "address": "0x" + uuid.uuid4().hex[:40],
            "created_at": datetime.datetime.utcnow().isoformat(),
        })
    return rows

def gen_base_donor(n, wallets):
    rows = []
    for i in range(n):
        wid = random.choice(wallets)["id"] if wallets else str(uuid.uuid4())
        rows.append({
            "id": str(uuid.uuid4()),
            "username": f"donor_{i}",
            "reputation": round(random.random() * 100, 2),
            "joined_at": datetime.datetime.utcnow().isoformat(),
            "wallet_id": wid,
        })
    return rows

def gen_basic_rows(n, prefix):
    rows = []
    for i in range(n):
        rows.append({
            "id": str(uuid.uuid4()),
            "name": f"{prefix}_{i}",
            "created_at": datetime.datetime.utcnow().isoformat(),
        })
    return rows

def gen_donations(n, donors, proposals):
    rows = []
    for i in range(n):
        donor = random.choice(donors)["id"] if donors else str(uuid.uuid4())
        proposal = random.choice(proposals)["id"] if proposals else str(uuid.uuid4())
        amt = round(random.expovariate(1/100), 6)
        rows.append({
            "id": str(uuid.uuid4()),
            "donor_id": donor,
            "proposal_id": proposal,
            "amount": amt,
            "created_at": datetime.datetime.utcnow().isoformat(),
        })
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="doncoin/data_science/data_pg", help="output dir")
    parser.add_argument("--counts", type=int, default=200, help="approx rows per table")
    args = parser.parse_args()

    out = os.path.abspath(args.out)
    n = args.counts

    # wallets
    wallets = gen_base_wallet(max(10, int(n/10)))
    write_csv(os.path.join(out, "base_wallet.csv"), ["id","address","created_at"], wallets)

    donors = gen_base_donor(n, wallets)
    write_csv(os.path.join(out, "base_donor.csv"), ["id","username","reputation","joined_at","wallet_id"], donors)

    proposals = gen_basic_rows(max(5, int(n/20)), "proposal")
    write_csv(os.path.join(out, "base_proposal.csv"), ["id","name","created_at"], proposals)

    rounds = gen_basic_rows(max(3, int(n/50)), "round")
    write_csv(os.path.join(out, "base_round.csv"), ["id","name","created_at"], rounds)

    matchingpool = gen_basic_rows(max(3, int(n/50)), "matchingpool")
    write_csv(os.path.join(out, "base_matchingpool.csv"), ["id","name","created_at"], matchingpool)

    donations = gen_donations(n, donors, proposals)
    write_csv(os.path.join(out, "base_donation.csv"), ["id","donor_id","proposal_id","amount","created_at"], donations)

    # matches, payouts, qfresults, sybilscore, governancetoken
    matches = gen_basic_rows(max(5, int(n/20)), "match")
    write_csv(os.path.join(out, "base_match.csv"), ["id","name","created_at"], matches)

    payouts = gen_basic_rows(max(5, int(n/20)), "payout")
    write_csv(os.path.join(out, "base_payout.csv"), ["id","name","created_at"], payouts)

    qf = gen_basic_rows(max(5, int(n/20)), "qfresult")
    write_csv(os.path.join(out, "base_qfresult.csv"), ["id","name","created_at"], qf)

    syb = gen_basic_rows(max(10, int(n/10)), "sybilscore")
    write_csv(os.path.join(out, "base_sybilscore.csv"), ["id","name","created_at"], syb)

    gtok = gen_basic_rows(max(5, int(n/20)), "governancetoken")
    write_csv(os.path.join(out, "base_governancetoken.csv"), ["id","name","created_at"], gtok)

    print(f"Generated CSVs in {out}")

if __name__ == '__main__':
    main()

import os
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta
from faker import Faker
import uuid
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()


from base.models import (
    Wallet, Donor, SybilScore, MatchingPool, Round,
    Proposal, Donation, Match, QFResult, Payout, ContractEvent,
    GovernanceToken
)

fake = Faker()

NUM_WALLETS = 10
NUM_DONORS = 15
NUM_POOLS = 3
NUM_ROUNDS = 5
NUM_PROPOSALS = 20
NUM_DONATIONS = 50
NUM_EVENTS = 30
import uuid


def create_wallets():
    wallets = []
    for _ in range(NUM_WALLETS):
        wallet = Wallet.objects.create(
            address=str(uuid.uuid4()),
            balance=Decimal(random.uniform(0, 10000)).quantize(Decimal('0.00000001')),
            status=random.choice(['active', 'frozen', 'flagged'])
        )
        wallets.append(wallet)
    return wallets

def create_donors(wallets):
    donors = []
    for _ in range(NUM_DONORS):
        wallet = random.choice(wallets)
        donor = Donor.objects.create(
            wallet=wallet,
            username=fake.unique.user_name(),
            reputation_score=round(random.uniform(0, 100), 2)
        )
        donors.append(donor)
    return donors

def create_sybil_scores(wallets):
    for wallet in wallets:
        for _ in range(random.randint(1, 3)):
            SybilScore.objects.create(
                wallet=wallet,
                score=round(random.uniform(0, 1), 2),
                verified_by=fake.name()
            )

def create_matching_pools():
    pools = []
    for _ in range(NUM_POOLS):
        pool = MatchingPool.objects.create(
            total_funds=Decimal(random.uniform(10000, 50000)).quantize(Decimal('0.00000001')),
            allocated_funds=Decimal(random.uniform(0, 10000)).quantize(Decimal('0.00000001')),
            replenished_by=fake.name()
        )
        pools.append(pool)
    return pools

def create_rounds(pools):
    rounds = []
    for pool in pools:
        for _ in range(random.randint(1, NUM_ROUNDS)):
            start = fake.date_time_this_year()
            end = start + timedelta(days=random.randint(1, 30))
            rnd = Round.objects.create(
                start_date=start,
                end_date=end,
                matching_pool=pool,
                status=random.choice(['active', 'closed', 'upcoming'])
            )
            rounds.append(rnd)
    return rounds

def create_proposals(donors, rounds):
    proposals = []
    for _ in range(NUM_PROPOSALS):
        donor = random.choice(donors)
        rnd = random.choice(rounds)
        proposal = Proposal.objects.create(
            title=fake.sentence(nb_words=6),
            description=fake.paragraph(nb_sentences=3),
            proposer=donor,
            round=rnd,
            status=random.choice(['pending', 'approved', 'rejected', 'funded']),
            total_donations=Decimal(random.uniform(0, 5000)).quantize(Decimal('0.00000001'))
        )
        proposals.append(proposal)
    return proposals

def create_donations(donors, proposals):
    for _ in range(NUM_DONATIONS):
        donor = random.choice(donors)
        proposal = random.choice(proposals)
        Donation.objects.create(
            donor=donor,
            proposal=proposal,
            amount=Decimal(random.uniform(10, 1000)).quantize(Decimal('0.00000001')),
            sybil_score=round(random.uniform(0, 1), 2),
            tx_hash=fake.unique.sha256()
        )

def create_matches(proposals, rounds):
    for proposal in proposals:
        rnd = random.choice(rounds)
        Match.objects.create(
            proposal=proposal,
            round=rnd,
            matched_amount=Decimal(random.uniform(0, 1000)).quantize(Decimal('0.00000001'))
        )

def create_qf_results(proposals, rounds):
    for proposal in proposals:
        rnd = random.choice(rounds)
        QFResult.objects.create(
            proposal=proposal,
            round=rnd,
            calculated_match=Decimal(random.uniform(0, 500)).quantize(Decimal('0.00000001')),
            verified=random.choice([True, False])
        )

def create_payouts(proposals, rounds):
    for proposal in proposals:
        rnd = random.choice(rounds)
        Payout.objects.create(
            proposal=proposal,
            round=rnd,
            amount=Decimal(random.uniform(10, 500)).quantize(Decimal('0.00000001')),
            tx_hash=fake.unique.sha256()
        )

def create_contract_events(proposals, rounds):
    for _ in range(NUM_EVENTS):
        proposal = random.choice(proposals + [None])
        rnd = random.choice(rounds + [None])
        ContractEvent.objects.create(
            event_type=fake.word(),
            round=rnd,
            proposal=proposal,
            timestamp=fake.date_time_this_year(),
            tx_hash=fake.unique.sha256()
        )

def create_governance_tokens(wallets):
    roles = ['member', 'admin', 'council']
    for wallet in wallets:
        for role in roles:
            GovernanceToken.objects.create(
                wallet=wallet,
                voting_power=Decimal(random.uniform(0, 1000)).quantize(Decimal('0.00000001')),
                role=role
            )

if __name__ == "__main__":
    print("Seeding data...")
    wallets = create_wallets()
    donors = create_donors(wallets)
    create_sybil_scores(wallets)
    pools = create_matching_pools()
    rounds = create_rounds(pools)
    proposals = create_proposals(donors, rounds)
    create_donations(donors, proposals)
    create_matches(proposals, rounds)
    create_qf_results(proposals, rounds)
    create_payouts(proposals, rounds)
    create_contract_events(proposals, rounds)
    create_governance_tokens(wallets)
    print("Seeding complete!")






from django.db import models
from django.core.validators import MinValueValidator
import uuid

class Wallet(models.Model):
    WALLET_STATUS = [
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('flagged', 'Flagged'),
    ]
    
    wallet_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=255, unique=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    status = models.CharField(max_length=10, choices=WALLET_STATUS, default='active')
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.address} ({self.status})"

class Donor(models.Model):
    donor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='donors')  # owns
    username = models.CharField(max_length=100, unique=True)
    reputation_score = models.FloatField(default=0.0)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class SybilScore(models.Model):
    score_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='sybil_scores')  # gets
    score = models.FloatField(default=0.0)
    verified_by = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['wallet', 'verified_by']

    def __str__(self):
        return f"Sybil Score: {self.score} for {self.wallet.address}"

class MatchingPool(models.Model):
    pool_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    total_funds = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    allocated_funds = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    replenished_by = models.CharField(max_length=100)

    def __str__(self):
        return f"Pool {self.pool_id} - Total: {self.total_funds}"

class Round(models.Model):
    ROUND_STATUS = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('upcoming', 'Upcoming'),
    ]
    
    round_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    matching_pool = models.ForeignKey(MatchingPool, on_delete=models.CASCADE, related_name='rounds')  # funds
    status = models.CharField(max_length=10, choices=ROUND_STATUS, default='upcoming')

    def __str__(self):
        return f"Round {self.round_id} ({self.status})"

class Proposal(models.Model):
    PROPOSAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('funded', 'Funded'),
    ]
    
    proposal_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    proposer = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='proposals')  # makes
    status = models.CharField(max_length=10, choices=PROPOSAL_STATUS, default='pending')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='proposals')  # contains
    total_donations = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Donation(models.Model):
    donation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')  # backs
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='donations')  # receives
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    sybil_score = models.FloatField(default=0.0)
    tx_hash = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation {self.donation_id} - {self.amount}"

class Match(models.Model):
    match_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='matches')  # receives
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='matches')  # has
    matched_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)

    class Meta:
        unique_together = ['proposal', 'round']

    def __str__(self):
        return f"Match {self.match_id} - {self.matched_amount}"

class QFResult(models.Model):
    result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='qf_results')  # produces
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='qf_results')  # produces
    calculated_match = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ['round', 'proposal']

    def __str__(self):
        return f"QF Result for {self.proposal.title} - {self.calculated_match}"

class Payout(models.Model):
    payout_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='payouts')  # receives
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='payouts')  # issues
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    tx_hash = models.CharField(max_length=255, unique=True)
    distributed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payout {self.payout_id} - {self.amount}"

class ContractEvent(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='contract_events', null=True, blank=True)  # logs
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='contract_events', null=True, blank=True)  # logs
    timestamp = models.DateTimeField()
    tx_hash = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.event_type} - {self.tx_hash}"

class GovernanceToken(models.Model):
    ROLES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('council', 'Council'),
    ]
    
    holder_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='governance_tokens')  # has
    voting_power = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    role = models.CharField(max_length=10, choices=ROLES, default='member')

    class Meta:
        unique_together = ['wallet', 'role']

    def __str__(self):
        return f"{self.wallet.address} - {self.role} ({self.voting_power})"
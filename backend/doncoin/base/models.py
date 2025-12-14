from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
import uuid

# --- Custom User Manager ---
class DonorManager(BaseUserManager):
    def create_user(self, wallet, password=None, **extra_fields):
        if not wallet:
            raise ValueError('The Wallet field must be set')
        
        # We don't really use email/username in the traditional sense, 
        # but Django requires a unique identifier. Ideally, wallet address is unique.
        user = self.model(wallet=wallet, **extra_fields)
        user.set_unusable_password() # Web3 users don't have passwords
        user.save(using=self._db)
        return user

    def create_superuser(self, wallet, password=None, **extra_fields):
        # For admin access, we might need a workaround or just use wallet auth + is_superuser flag
        # But for 'createsuperuser' command to work, we'll need basic fields.
        # This is tricky with pure wallet auth. 
        # Recommendation: Use a dummy wallet or ensure the wallet exists first.
        # For simplicity in this refactor, we assume superuser creation via command line might need a hack 
        # or we just rely on updating DB directly.
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(wallet, password, **extra_fields)

# --- Core Models ---

class ChainSession(models.Model):
    """Tracks each Hardhat/blockchain node instance.
    When contracts are redeployed, a new session is created.
    Data is filtered by active session to avoid showing stale proposals.
    
    Uses address + deployment_block_hash to uniquely identify a session.
    Block hashes are unique even when block numbers and addresses are the same
    (which happens with Hardhat's deterministic deployment).
    """
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant_registry_address = models.CharField(max_length=255, help_text="Address of GrantRegistry contract for this session")
    deployment_block = models.IntegerField(default=0, help_text="Block number when GrantRegistry was deployed")
    deployment_block_hash = models.CharField(max_length=66, default='', help_text="Hash of deployment block - unique per node session")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        # Same address with different block hash = different sessions (node restarted)
        unique_together = ('grant_registry_address', 'deployment_block_hash')

    def __str__(self):
        return f"Session {self.session_id} (block {self.deployment_block}, {'active' if self.is_active else 'inactive'})"

    @classmethod
    def get_or_create_for_deployment(cls, grant_registry_address, deployment_block=0, deployment_block_hash=''):
        """Get existing session for address+block_hash or create new one, deactivating others."""
        session, created = cls.objects.get_or_create(
            grant_registry_address=grant_registry_address,
            deployment_block_hash=deployment_block_hash,
            defaults={'is_active': True, 'deployment_block': deployment_block}
        )
        if created:
            # Deactivate all other sessions
            cls.objects.exclude(session_id=session.session_id).update(is_active=False)
        return session, created


class Wallet(models.Model):
    wallet_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=255, unique=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0.0, help_text="Read-only cache of on-chain balance")
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('flagged', 'Flagged'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', db_index=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.address

class Donor(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model representing a Donor/User in the system.
    Authentication is primary via Wallet signature.
    """
    donor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identity
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE, related_name='donor')
    username = models.CharField(max_length=100, unique=True, blank=True, null=True) # Optional display name
    
    # Profile
    reputation_score = models.FloatField(default=0.0)
    joined_at = models.DateTimeField(auto_now_add=True)

    # Permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # For admin site access

    objects = DonorManager()

    USERNAME_FIELD = 'wallet' # Authenticate via wallet relation (or address)
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or self.wallet.address

    @property
    def address(self):
        return self.wallet.address


class MatchingPool(models.Model):
    pool_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    total_funds = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    allocated_funds = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    replenished_by = models.CharField(max_length=100) # e.g., "Grant DAO"

    def __str__(self):
        return f"Pool {self.pool_id} - {self.total_funds} ETH"

class Round(models.Model):
    round_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matching_pool = models.ForeignKey(MatchingPool, on_delete=models.CASCADE, related_name='rounds')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('upcoming', 'Upcoming'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming')

    def __str__(self):
        return f"Round {self.start_date.date()} - {self.status}"

class Proposal(models.Model):
    proposal_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposer = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='proposals')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='proposals')
    chain_session = models.ForeignKey(ChainSession, on_delete=models.CASCADE, related_name='proposals', null=True, blank=True)
    
    on_chain_id = models.IntegerField(null=True, blank=True)  # Removed unique constraint - can repeat across sessions
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('funded', 'Funded'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    funding_goal = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    total_donations = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Donation(models.Model):
    donation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} from {self.donor} to {self.proposal}"

class Match(models.Model):
    match_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='matches')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='matches')
    matched_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)

    class Meta:
        unique_together = ('proposal', 'round')

class QFResult(models.Model):
    result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='qf_results')
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='qf_results')
    calculated_match = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('round', 'proposal')

class Payout(models.Model):
    payout_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='payouts')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    tx_hash = models.CharField(max_length=255, unique=True, db_index=True)
    distributed_at = models.DateTimeField(auto_now_add=True)

class ContractEvent(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chain_session = models.ForeignKey(ChainSession, on_delete=models.CASCADE, related_name='contract_events', null=True, blank=True)
    event_type = models.CharField(max_length=100) # e.g. "DonationReceived", "RoundStarted"
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='contract_events', null=True, blank=True)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='contract_events', null=True, blank=True)
    timestamp = models.DateTimeField()
    tx_hash = models.CharField(max_length=255, db_index=True)  # Removed unique - can repeat across sessions

# --- Sybil Resistance (Optional) ---
class SybilScore(models.Model):
    score_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='sybil_scores')
    score = models.FloatField(default=0.0) # 0.0 to 1.0
    verified_by = models.CharField(max_length=100) # e.g., "GitcoinPassport"
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('wallet', 'verified_by')

# --- Governance (Optional Structure) ---
class GovernanceToken(models.Model):
    holder_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='governance_tokens')
    voting_power = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('council', 'Council'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    
    class Meta:
        unique_together = ('wallet', 'role')
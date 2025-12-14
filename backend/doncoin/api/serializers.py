from rest_framework import serializers
from django.db.models import Sum
from base.models import (
    Wallet, Donor, SybilScore, MatchingPool, Round, Proposal,
    Donation, Match, QFResult, Payout, ContractEvent, GovernanceToken
)

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            'wallet_id', 'address', 'balance', 'status', 'last_activity'
        ]
        read_only_fields = ['wallet_id', 'last_activity']


class DonorSerializer(serializers.ModelSerializer):
    wallet_details = WalletSerializer(source='wallet', read_only=True)
    total_donations = serializers.SerializerMethodField()
    total_proposals = serializers.SerializerMethodField()
    
    # Expose wallet address directly for convenience
    address = serializers.SerializerMethodField()

    class Meta:
        model = Donor
        fields = [
            'donor_id', 'wallet', 'wallet_details', 'address', 'username', 
            'reputation_score', 'joined_at', 'total_donations', 'total_proposals',
            'is_staff'
        ]
        read_only_fields = ['donor_id', 'joined_at', 'is_staff']

    def get_address(self, obj):
        return obj.address

    def get_total_donations(self, obj):
        try:
            return obj.donations.aggregate(total=Sum('amount'))['total'] or 0
        except:
            return 0

    def get_total_proposals(self, obj):
        try:
            return obj.proposals.count()
        except:
            return 0


class SybilScoreSerializer(serializers.ModelSerializer):
    wallet_address = serializers.CharField(source='wallet.address', read_only=True)

    class Meta:
        model = SybilScore
        fields = [
            'score_id', 'wallet', 'wallet_address', 'score', 
            'verified_by', 'last_updated'
        ]
        read_only_fields = ['score_id', 'last_updated']


class MatchingPoolSerializer(serializers.ModelSerializer):
    available_funds = serializers.SerializerMethodField()
    total_rounds = serializers.SerializerMethodField()

    class Meta:
        model = MatchingPool
        fields = [
            'pool_id', 'total_funds', 'allocated_funds', 
            'available_funds', 'replenished_by', 'total_rounds'
        ]
        read_only_fields = ['pool_id']

    def get_available_funds(self, obj):
        return obj.total_funds - obj.allocated_funds

    def get_total_rounds(self, obj):
        return obj.rounds.count()


class RoundSerializer(serializers.ModelSerializer):
    matching_pool_details = MatchingPoolSerializer(source='matching_pool', read_only=True)
    is_active = serializers.SerializerMethodField()
    total_proposals = serializers.SerializerMethodField()
    total_donations = serializers.SerializerMethodField()
    
    # Frontend compatibility fields
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    pool = serializers.SerializerMethodField()
    endDate = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = [
            'round_id', 'start_date', 'end_date', 'matching_pool',
            'matching_pool_details', 'status', 'is_active',
            'total_proposals', 'total_donations',
            # Frontend compatibility fields
            'id', 'name', 'pool', 'endDate'
        ]
        read_only_fields = ['round_id']

    def get_is_active(self, obj):
        from django.utils import timezone
        now = timezone.now()
        if obj.start_date and obj.end_date:
            return obj.start_date <= now <= obj.end_date and obj.status == 'active'
        return False

    def get_total_proposals(self, obj):
        return obj.proposals.count()

    def get_total_donations(self, obj):
        total = 0
        try:
            for proposal in obj.proposals.all():
                total += proposal.donations.aggregate(total=Sum('amount'))['total'] or 0
        except:
            pass
        return total
    
    # Frontend compatibility methods
    def get_id(self, obj):
        return f"round-{obj.round_id}"
    
    def get_name(self, obj):
        return f"Round {str(obj.round_id)[:8]}" if obj.round_id else "Active Round"
    
    def get_pool(self, obj):
        if obj.matching_pool:
            return float(obj.matching_pool.total_funds)
        return 0.0
    
    def get_endDate(self, obj):
        return obj.end_date.isoformat() if obj.end_date else None



class ProposalSerializer(serializers.ModelSerializer):
    proposer_details = DonorSerializer(source='proposer', read_only=True)
    round_details = RoundSerializer(source='round', read_only=True)
    total_funding = serializers.SerializerMethodField()
    donation_count = serializers.SerializerMethodField()
    match_amount = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            'proposal_id', 'title', 'description', 'proposer', 'proposer_details',
            'status', 'round', 'round_details', 'funding_goal', 'total_donations', 'created_at',
            'total_funding', 'donation_count', 'match_amount', 'on_chain_id'
        ]
        read_only_fields = ['proposal_id', 'created_at', 'total_donations', 'proposer', 'round', 'on_chain_id']

    def get_total_funding(self, obj):
        donations_total = obj.donations.aggregate(total=Sum('amount'))['total'] or 0
        match_total = obj.matches.aggregate(total=Sum('matched_amount'))['total'] or 0
        return donations_total + match_total

    def get_donation_count(self, obj):
        return obj.donations.count()

    def get_match_amount(self, obj):
        return obj.matches.aggregate(total=Sum('matched_amount'))['total'] or 0


class DonationSerializer(serializers.ModelSerializer):
    donor_details = DonorSerializer(source='donor', read_only=True)
    proposal_title = serializers.CharField(source='proposal.title', read_only=True)
    round_id = serializers.UUIDField(source='proposal.round.round_id', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'donation_id', 'donor', 'donor_details', 'proposal', 'proposal_title',
            'round_id', 'amount', 'description', 'created_at'
        ]
        read_only_fields = ['donation_id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Donation amount must be positive")
        return value


class MatchSerializer(serializers.ModelSerializer):
    proposal_title = serializers.CharField(source='proposal.title', read_only=True)
    round_details = RoundSerializer(source='round', read_only=True)
    proposal_details = ProposalSerializer(source='proposal', read_only=True)

    class Meta:
        model = Match
        fields = [
            'match_id', 'proposal', 'proposal_title', 'proposal_details',
            'round', 'round_details', 'matched_amount'
        ]
        read_only_fields = ['match_id']


class QFResultSerializer(serializers.ModelSerializer):
    proposal_title = serializers.CharField(source='proposal.title', read_only=True)
    round_details = RoundSerializer(source='round', read_only=True)
    proposal_details = ProposalSerializer(source='proposal', read_only=True)

    class Meta:
        model = QFResult
        fields = [
            'result_id', 'round', 'round_details', 'proposal', 'proposal_title',
            'proposal_details', 'calculated_match', 'verified'
        ]
        read_only_fields = ['result_id']


class PayoutSerializer(serializers.ModelSerializer):
    proposal_title = serializers.CharField(source='proposal.title', read_only=True)
    round_details = RoundSerializer(source='round', read_only=True)
    proposal_details = ProposalSerializer(source='proposal', read_only=True)

    class Meta:
        model = Payout
        fields = [
            'payout_id', 'proposal', 'proposal_title', 'proposal_details',
            'round', 'round_details', 'amount', 'tx_hash', 'distributed_at'
        ]
        read_only_fields = ['payout_id', 'distributed_at']


class ContractEventSerializer(serializers.ModelSerializer):
    round_details = RoundSerializer(source='round', read_only=True)
    proposal_title = serializers.CharField(source='proposal.title', read_only=True, allow_null=True)
    proposal_details = ProposalSerializer(source='proposal', read_only=True)

    class Meta:
        model = ContractEvent
        fields = [
            'event_id', 'event_type', 'round', 'round_details', 'proposal',
            'proposal_title', 'proposal_details', 'timestamp', 'tx_hash'
        ]
        read_only_fields = ['event_id']


class GovernanceTokenSerializer(serializers.ModelSerializer):
    wallet_address = serializers.CharField(source='wallet.address', read_only=True)
    wallet_details = WalletSerializer(source='wallet', read_only=True)

    class Meta:
        model = GovernanceToken
        fields = [
            'holder_id', 'wallet', 'wallet_address', 'wallet_details',
            'voting_power', 'role'
        ]
        read_only_fields = ['holder_id']
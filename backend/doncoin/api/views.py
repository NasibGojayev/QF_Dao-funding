from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F
from django_filters.rest_framework import DjangoFilterBackend

# Import from current directory (api) and parent directory (models)
from .serializers import *
from base.models import (
    Wallet, Donor, SybilScore, MatchingPool, Round, Proposal,
    Donation, Match, QFResult, Payout, ContractEvent, GovernanceToken
)


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all().order_by('-last_activity')
    serializer_class = WalletSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['address']
    ordering_fields = ['balance', 'last_activity']
    ordering = ['-last_activity']

    @action(detail=True, methods=['get'])
    def donor_info(self, request, pk=None):
        """Get all donors associated with this wallet"""
        wallet = self.get_object()
        donors = wallet.donors.all()
        serializer = DonorSerializer(donors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sybil_scores(self, request, pk=None):
        """Get sybil scores for this wallet"""
        wallet = self.get_object()
        scores = wallet.sybil_scores.all()
        serializer = SybilScoreSerializer(scores, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def governance_tokens(self, request, pk=None):
        """Get governance tokens held by this wallet"""
        wallet = self.get_object()
        tokens = wallet.governance_tokens.all()
        serializer = GovernanceTokenSerializer(tokens, many=True)
        return Response(serializer.data)


class DonorViewSet(viewsets.ModelViewSet):
    queryset = Donor.objects.all().order_by('-joined_at')
    serializer_class = DonorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'wallet__address']
    ordering_fields = ['reputation_score', 'joined_at']
    ordering = ['-reputation_score']

    @action(detail=True, methods=['get'])
    def donations(self, request, pk=None):
        """Get all donations made by this donor"""
        donor = self.get_object()
        donations = donor.donations.all().order_by('-created_at')
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def proposals(self, request, pk=None):
        """Get all proposals created by this donor"""
        donor = self.get_object()
        proposals = donor.proposals.all().order_by('-created_at')
        serializer = ProposalSerializer(proposals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_donors(self, request):
        """Get top donors by total donation amount"""
        top_donors = Donor.objects.annotate(
            total_donated=Sum('donations__amount')
        ).filter(total_donated__gt=0).order_by('-total_donated')[:10]
        serializer = DonorSerializer(top_donors, many=True)
        return Response(serializer.data)


class SybilScoreViewSet(viewsets.ModelViewSet):
    queryset = SybilScore.objects.all().order_by('-last_updated')
    serializer_class = SybilScoreSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['score', 'last_updated']
    ordering = ['-last_updated']


class MatchingPoolViewSet(viewsets.ModelViewSet):
    queryset = MatchingPool.objects.all()
    serializer_class = MatchingPoolSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['total_funds', 'allocated_funds']

    @action(detail=True, methods=['get'])
    def rounds(self, request, pk=None):
        """Get all rounds funded by this matching pool"""
        matching_pool = self.get_object()
        rounds = matching_pool.rounds.all().order_by('-start_date')
        serializer = RoundSerializer(rounds, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_funds(self, request, pk=None):
        """Add funds to the matching pool"""
        matching_pool = self.get_object()
        amount = request.data.get('amount')
        
        if not amount or float(amount) <= 0:
            return Response(
                {'error': 'Valid positive amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        matching_pool.total_funds += float(amount)
        matching_pool.save()
        
        serializer = self.get_serializer(matching_pool)
        return Response(serializer.data)


class RoundViewSet(viewsets.ModelViewSet):
    queryset = Round.objects.all().order_by('-start_date')
    serializer_class = RoundSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']

    @action(detail=True, methods=['get'])
    def proposals(self, request, pk=None):
        """Get all proposals in this round"""
        round_obj = self.get_object()
        proposals = round_obj.proposals.all().order_by('-created_at')
        serializer = ProposalSerializer(proposals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def donations(self, request, pk=None):
        """Get all donations in this round"""
        round_obj = self.get_object()
        donations = Donation.objects.filter(proposal__round=round_obj).order_by('-created_at')
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def donations_summary(self, request, pk=None):
        """Get summary of donations for all proposals in this round"""
        round_obj = self.get_object()
        proposals = round_obj.proposals.annotate(
            total_donated=Sum('donations__amount'),
            donation_count=Count('donations'),
            unique_donors=Count('donations__donor', distinct=True)
        )
        
        data = []
        for proposal in proposals:
            data.append({
                'proposal_id': proposal.proposal_id,
                'title': proposal.title,
                'status': proposal.status,
                'total_donated': proposal.total_donated or 0,
                'donation_count': proposal.donation_count,
                'unique_donors': proposal.unique_donors,
                'proposer': proposal.proposer.username
            })
        
        total_round_donations = sum(item['total_donated'] for item in data)
        
        return Response({
            'round_id': round_obj.round_id,
            'total_donations': total_round_donations,
            'total_proposals': len(data),
            'proposals': data
        })

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """Get all matches for this round"""
        round_obj = self.get_object()
        matches = round_obj.matches.all()
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def calculate_qf(self, request, pk=None):
        """Trigger quadratic funding calculation for this round"""
        round_obj = self.get_object()
        
        # Basic QF calculation (simplified)
        proposals = round_obj.proposals.annotate(
            total_donated=Sum('donations__amount'),
            donation_count=Count('donations')
        )
        
        # Calculate quadratic funding matches
        results = []
        for proposal in proposals:
            if proposal.total_donated and proposal.total_donated > 0:
                # Simple QF formula: match = (sum of sqrt(donation))^2
                donation_roots = sum((donation.amount ** 0.5) for donation in proposal.donations.all())
                match_amount = (donation_roots ** 2) - proposal.total_donated
                
                if match_amount > 0:
                    # Create or update QFResult
                    qf_result, created = QFResult.objects.update_or_create(
                        round=round_obj,
                        proposal=proposal,
                        defaults={
                            'calculated_match': match_amount,
                            'verified': False
                        }
                    )
                    results.append({
                        'proposal': proposal.title,
                        'match_amount': match_amount,
                        'verified': qf_result.verified
                    })
        
        return Response({
            "message": f"QF calculation completed for round {round_obj.round_id}",
            "results": results
        })

    @action(detail=True, methods=['get'])
    def qf_results(self, request, pk=None):
        """Get QF results for this round"""
        round_obj = self.get_object()
        results = round_obj.qf_results.all()
        serializer = QFResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active_rounds(self, request):
        """Get all active rounds"""
        from django.utils import timezone
        now = timezone.now()
        active_rounds = Round.objects.filter(
            start_date__lte=now, 
            end_date__gte=now, 
            status='active'
        ).order_by('end_date')
        serializer = RoundSerializer(active_rounds, many=True)
        return Response(serializer.data)


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all().order_by('-created_at')
    serializer_class = ProposalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'total_donations']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def donations(self, request, pk=None):
        """Get all donations for this proposal"""
        proposal = self.get_object()
        donations = proposal.donations.all().order_by('-created_at')
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """Get all matches for this proposal"""
        proposal = self.get_object()
        matches = proposal.matches.all()
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def funding_summary(self, request, pk=None):
        """Get detailed funding summary for this proposal"""
        proposal = self.get_object()
        total_donations = proposal.donations.aggregate(total=Sum('amount'))['total'] or 0
        total_matches = proposal.matches.aggregate(total=Sum('matched_amount'))['total'] or 0
        donation_count = proposal.donations.count()
        unique_donors = proposal.donations.values('donor').distinct().count()
        
        return Response({
            'proposal_id': proposal.proposal_id,
            'title': proposal.title,
            'total_donations': total_donations,
            'total_matches': total_matches,
            'total_funding': total_donations + total_matches,
            'donation_count': donation_count,
            'unique_donors': unique_donors,
            'status': proposal.status
        })

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update proposal status"""
        proposal = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Proposal.PROPOSAL_STATUS):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.status = new_status
        proposal.save()
        
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending proposals (most donations in last 7 days)"""
        from django.utils import timezone
        from datetime import timedelta
        
        week_ago = timezone.now() - timedelta(days=7)
        trending_proposals = Proposal.objects.filter(
            donations__created_at__gte=week_ago
        ).annotate(
            recent_donations=Count('donations'),
            recent_amount=Sum('donations__amount')
        ).filter(recent_amount__gt=0).order_by('-recent_amount')[:10]
        
        serializer = ProposalSerializer(trending_proposals, many=True)
        return Response(serializer.data)


class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.all().order_by('-created_at')
    serializer_class = DonationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def recent_large_donations(self, request):
        """Get recent large donations (above threshold)"""
        threshold = request.query_params.get('threshold', 100)
        large_donations = Donation.objects.filter(
            amount__gte=threshold
        ).order_by('-created_at')[:20]
        serializer = DonationSerializer(large_donations, many=True)
        return Response(serializer.data)


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['matched_amount']
    ordering = ['-matched_amount']


class QFResultViewSet(viewsets.ModelViewSet):
    queryset = QFResult.objects.all()
    serializer_class = QFResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['calculated_match']
    ordering = ['-calculated_match']

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a QF result"""
        qf_result = self.get_object()
        qf_result.verified = True
        qf_result.save()
        
        serializer = self.get_serializer(qf_result)
        return Response(serializer.data)


class PayoutViewSet(viewsets.ModelViewSet):
    queryset = Payout.objects.all().order_by('-distributed_at')
    serializer_class = PayoutSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['amount', 'distributed_at']
    ordering = ['-distributed_at']

    @action(detail=False, methods=['get'])
    def recent_payouts(self, request):
        """Get recent payouts"""
        recent_payouts = Payout.objects.all().order_by('-distributed_at')[:20]
        serializer = PayoutSerializer(recent_payouts, many=True)
        return Response(serializer.data)


class ContractEventViewSet(viewsets.ModelViewSet):
    queryset = ContractEvent.objects.all().order_by('-timestamp')
    serializer_class = ContractEventSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['event_type', 'tx_hash']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get events by type"""
        event_type = request.query_params.get('type')
        if event_type:
            events = ContractEvent.objects.filter(event_type=event_type).order_by('-timestamp')
            serializer = ContractEventSerializer(events, many=True)
            return Response(serializer.data)
        return Response([])


class GovernanceTokenViewSet(viewsets.ModelViewSet):
    queryset = GovernanceToken.objects.all()
    serializer_class = GovernanceTokenSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['voting_power']
    ordering = ['-voting_power']

    @action(detail=False, methods=['get'])
    def by_wallet(self, request):
        """Get governance tokens by wallet address"""
        wallet_address = request.query_params.get('wallet_address')
        if wallet_address:
            tokens = GovernanceToken.objects.filter(wallet__address=wallet_address)
            serializer = self.get_serializer(tokens, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get governance tokens by role"""
        role = request.query_params.get('role')
        if role in dict(GovernanceToken.ROLES):
            tokens = GovernanceToken.objects.filter(role=role).order_by('-voting_power')
            serializer = self.get_serializer(tokens, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=True, methods=['post'])
    def update_voting_power(self, request, pk=None):
        """Update voting power for a token holder"""
        token = self.get_object()
        new_power = request.data.get('voting_power')
        
        if new_power is None or float(new_power) < 0:
            return Response(
                {'error': 'Valid non-negative voting power is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token.voting_power = float(new_power)
        token.save()
        
        serializer = self.get_serializer(token)
        return Response(serializer.data)
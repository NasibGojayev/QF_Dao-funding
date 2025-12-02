from django.contrib import admin
from .models import (
    Wallet, Donor, SybilScore, MatchingPool, Round, Proposal,
    Donation, Match, QFResult, Payout, ContractEvent, GovernanceToken
)

# -----------------------
# INLINE DEFINITIONS
# -----------------------
class DonorInline(admin.TabularInline):
    model = Donor
    extra = 0

class SybilScoreInline(admin.TabularInline):
    model = SybilScore
    extra = 0

class ProposalInline(admin.TabularInline):
    model = Proposal
    extra = 0

class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0

class MatchInline(admin.TabularInline):
    model = Match
    extra = 0

class QFResultInline(admin.TabularInline):
    model = QFResult
    extra = 0

class PayoutInline(admin.TabularInline):
    model = Payout
    extra = 0

class ContractEventInline(admin.TabularInline):
    model = ContractEvent
    extra = 0


# -----------------------
# MODEL ADMINS
# -----------------------
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("address", "status", "balance", "last_activity")
    search_fields = ("address",)
    list_filter = ("status",)
    inlines = [DonorInline, SybilScoreInline]


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("username", "wallet", "reputation_score", "joined_at")
    search_fields = ("username", "wallet__address")
    list_filter = ("joined_at",)


@admin.register(SybilScore)
class SybilScoreAdmin(admin.ModelAdmin):
    list_display = ("wallet", "score", "verified_by", "last_updated")
    search_fields = ("verified_by", "wallet__address")
    list_filter = ("verified_by",)


@admin.register(MatchingPool)
class MatchingPoolAdmin(admin.ModelAdmin):
    list_display = ("pool_id", "total_funds", "allocated_funds", "replenished_by")
    search_fields = ("pool_id", "replenished_by")


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("round_id", "status", "start_date", "end_date", "matching_pool")
    search_fields = ("round_id",)
    list_filter = ("status", "start_date", "end_date")
    inlines = [ProposalInline, MatchInline, QFResultInline, PayoutInline, ContractEventInline]


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("title", "proposer", "round", "status", "total_donations", "created_at")
    search_fields = ("title", "proposer__username")
    list_filter = ("status", "round")
    inlines = [DonationInline]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("donor", "proposal", "amount", "sybil_score", "tx_hash", "created_at")
    search_fields = ("tx_hash", "donor__username", "proposal__title")
    list_filter = ("created_at",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("proposal", "round", "matched_amount")
    search_fields = ("proposal__title",)


@admin.register(QFResult)
class QFResultAdmin(admin.ModelAdmin):
    list_display = ("proposal", "round", "calculated_match", "verified")
    list_filter = ("verified",)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("proposal", "round", "amount", "tx_hash", "distributed_at")
    search_fields = ("tx_hash",)
    list_filter = ("distributed_at",)


@admin.register(ContractEvent)
class ContractEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "round", "proposal", "timestamp", "tx_hash")
    search_fields = ("event_type", "tx_hash")
    list_filter = ("event_type", "timestamp")


@admin.register(GovernanceToken)
class GovernanceTokenAdmin(admin.ModelAdmin):
    list_display = ("wallet", "role", "voting_power")
    search_fields = ("wallet__address",)
    list_filter = ("role",)

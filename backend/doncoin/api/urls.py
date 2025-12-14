from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'wallets', views.WalletViewSet)
router.register(r'donors', views.DonorViewSet)
router.register(r'sybil-scores', views.SybilScoreViewSet)
router.register(r'matching-pools', views.MatchingPoolViewSet)
router.register(r'rounds', views.RoundViewSet)
router.register(r'proposals', views.ProposalViewSet)
router.register(r'donations', views.DonationViewSet)
router.register(r'matches', views.MatchViewSet)
router.register(r'qf-results', views.QFResultViewSet)
router.register(r'payouts', views.PayoutViewSet)
router.register(r'contract-events', views.ContractEventViewSet)
router.register(r'governance-tokens', views.GovernanceTokenViewSet)

app_name = 'api'
from .auth_views import WalletLoginView
from .views_faucet import ClaimTokensView

urlpatterns = [
    path('', include(router.urls)),
    # path('users/', ...), # REMOVED
    path('auth/wallet/', WalletLoginView.as_view(), name='wallet-login'),
    path('wallets/<uuid:wallet_id>/update/', views.WalletUpdateView.as_view(), name='wallet-update'),
    path('faucet/', ClaimTokensView.as_view(), name='faucet'),
]

from django.urls import path
from .views import ReferralDetailsView, ReferralHistoryView, WalletView

urlpatterns = [
    path('details/', ReferralDetailsView.as_view(), name='referral_details'),
    path('history/', ReferralHistoryView.as_view(), name='referral_history'),
    path('wallet/', WalletView.as_view(), name='wallet_detail'),
]

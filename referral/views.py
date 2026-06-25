from django.db.models import Sum
from decimal import Decimal
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ReferralTransaction, WalletTransaction
from .serializers import (
    ReferralDetailsSerializer,
    ReferralTransactionSerializer,
    WalletTransactionSerializer,
)
from .services import get_or_create_wallet

_bearer = [{'Bearer': []}]


class ReferralDetailsView(generics.GenericAPIView):
    """GET /api/v1/referral/details/ — own referral code + earnings summary"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralDetailsSerializer

    @swagger_auto_schema(
        operation_id='referral_details',
        operation_summary='Get referral details',
        operation_description=(
            'Returns the authenticated user\'s referral code, total number of successful '
            'referrals, total earnings, and current wallet balance.'
        ),
        tags=['Referral'],
        security=_bearer,
        responses={
            200: openapi.Response(
                description='Referral details',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'referral_code': openapi.Schema(type=openapi.TYPE_STRING, example='A3F9C12B'),
                        'total_referrals': openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                        'total_earnings': openapi.Schema(type=openapi.TYPE_STRING, example='250.00'),
                        'wallet_balance': openapi.Schema(type=openapi.TYPE_STRING, example='250.00'),
                    }
                )
            ),
            401: 'Authentication required',
        }
    )
    def get(self, request):
        user = request.user
        profile = user.profile
        wallet = get_or_create_wallet(user)

        rewarded_qs = ReferralTransaction.objects.filter(
            referrer=user, status='rewarded'
        )
        total_earnings = rewarded_qs.aggregate(
            total=Sum('reward_amount')
        )['total'] or Decimal('0.00')

        data = {
            'referral_code': profile.referral_code,
            'total_referrals': rewarded_qs.count(),
            'total_earnings': total_earnings,
            'wallet_balance': wallet.balance,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)


class ReferralHistoryView(generics.GenericAPIView):
    """GET /api/v1/referral/history/ — list all successful referrals made by user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralTransactionSerializer

    @swagger_auto_schema(
        operation_id='referral_history',
        operation_summary='Referral history',
        operation_description='Returns a list of all users referred by the authenticated user with reward status.',
        tags=['Referral'],
        security=_bearer,
        responses={
            200: ReferralTransactionSerializer(many=True),
            401: 'Authentication required',
        }
    )
    def get(self, request):
        qs = ReferralTransaction.objects.filter(referrer=request.user).select_related('referred_user')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class WalletView(generics.GenericAPIView):
    """GET /api/v1/referral/wallet/ — wallet balance + transaction history"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletTransactionSerializer

    @swagger_auto_schema(
        operation_id='wallet_detail',
        operation_summary='Wallet balance & transactions',
        operation_description='Returns current wallet balance and full transaction history for the authenticated user.',
        tags=['Referral'],
        security=_bearer,
        responses={
            200: openapi.Response(
                description='Wallet info',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'balance': openapi.Schema(type=openapi.TYPE_STRING, example='250.00'),
                        'transactions': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'amount': openapi.Schema(type=openapi.TYPE_STRING),
                                    'transaction_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['credit', 'debit']),
                                    'remark': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                }
                            )
                        ),
                    }
                )
            ),
            401: 'Authentication required',
        }
    )
    def get(self, request):
        wallet = get_or_create_wallet(request.user)
        transactions = WalletTransaction.objects.filter(user=request.user)
        return Response({
            'balance': str(wallet.balance),
            'transactions': WalletTransactionSerializer(transactions, many=True).data,
        })

from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Wallet, WalletTransaction, ReferralTransaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('balance', 'updated_at')


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ('id', 'amount', 'transaction_type', 'remark', 'created_at')


class ReferralTransactionSerializer(serializers.ModelSerializer):
    referred_user_name = serializers.SerializerMethodField()
    referred_user_email = serializers.SerializerMethodField()

    class Meta:
        model = ReferralTransaction
        fields = ('id', 'referred_user_name', 'referred_user_email',
                  'reward_amount', 'status', 'created_at')

    def get_referred_user_name(self, obj):
        return obj.referred_user.get_full_name() or obj.referred_user.username

    def get_referred_user_email(self, obj):
        return obj.referred_user.email


class ReferralDetailsSerializer(serializers.Serializer):
    referral_code = serializers.CharField()
    total_referrals = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2)

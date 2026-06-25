from django.contrib import admin
from .models import Wallet, WalletTransaction, ReferralTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'remark', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(ReferralTransaction)
class ReferralTransactionAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'reward_amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('referrer__username', 'referred_user__username')
    readonly_fields = ('id', 'created_at')

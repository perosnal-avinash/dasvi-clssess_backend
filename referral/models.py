import uuid
from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'

    def __str__(self):
        return f"{self.user.username} — ₹{self.balance}"

    def credit(self, amount, remark=''):
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
        WalletTransaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type='credit',
            remark=remark,
        )


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    remark = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wallet Transaction'
        verbose_name_plural = 'Wallet Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.transaction_type} | ₹{self.amount}"


class ReferralTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('rewarded', 'Rewarded'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='referrals_made'
    )
    referred_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='referral_record'
    )
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Referral Transaction'
        verbose_name_plural = 'Referral Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.username} → {self.referred_user.username} | ₹{self.reward_amount} | {self.status}"

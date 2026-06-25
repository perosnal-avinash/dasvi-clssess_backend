import logging
import os
from decimal import Decimal

from django.db import transaction
from django.contrib.auth.models import User

from authentication.models import UserProfile
from .models import Wallet, ReferralTransaction

logger = logging.getLogger(__name__)


def get_reward_amount() -> Decimal:
    """Read reward amount from environment — no code change needed to update it."""
    return Decimal(os.environ.get('REFERRAL_REWARD_AMOUNT', '25'))


def is_referral_enabled() -> bool:
    return os.environ.get('REFERRAL_ENABLED', 'true').lower() == 'true'


def get_or_create_wallet(user: User) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def validate_referral_code(code: str, new_user_email: str) -> tuple[bool, str, User | None]:
    """
    Returns (is_valid, error_message, referrer_user).
    """
    if not code:
        return False, 'No referral code provided.', None

    try:
        profile = UserProfile.objects.select_related('user').get(referral_code__iexact=code)
    except UserProfile.DoesNotExist:
        return False, 'Invalid referral code.', None

    referrer = profile.user

    if referrer.email.lower() == new_user_email.lower():
        return False, 'Self-referral is not allowed.', None

    return True, '', referrer


@transaction.atomic
def process_referral_reward(referrer: User, referred_user: User) -> ReferralTransaction:
    """
    Credits the referral reward to the referrer's wallet and records the transaction.
    Called after the referred user is verified / registered successfully.
    Idempotent — won't double-credit if called twice for the same referred_user.
    """
    if not is_referral_enabled():
        logger.info('Referral system is disabled via REFERRAL_ENABLED env var.')
        return None

    if ReferralTransaction.objects.filter(referred_user=referred_user).exists():
        logger.warning(
            'Referral reward already processed for user %s — skipping.',
            referred_user.username,
        )
        return ReferralTransaction.objects.get(referred_user=referred_user)

    reward = get_reward_amount()

    referral_tx = ReferralTransaction.objects.create(
        referrer=referrer,
        referred_user=referred_user,
        reward_amount=reward,
        status='pending',
    )

    wallet = get_or_create_wallet(referrer)
    wallet.credit(
        amount=reward,
        remark=f'Referral reward for inviting {referred_user.get_full_name() or referred_user.username}',
    )

    referral_tx.status = 'rewarded'
    referral_tx.save(update_fields=['status'])

    logger.info(
        'Referral reward ₹%s credited to %s for referring %s',
        reward, referrer.username, referred_user.username,
    )
    return referral_tx

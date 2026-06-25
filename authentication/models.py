import uuid
from django.db import models
from django.contrib.auth.models import User


def generate_referral_code():
    return uuid.uuid4().hex[:8].upper()


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('school_teacher', 'School Teacher'),
        ('school_principle', 'School Principle'),
        ('admin', 'Admin'),
        ('account', 'Account'),
        ('marketing', 'Marketing'),
    ]

    DISTRICT_CHOICES = [
        ('patna', 'Patna'), ('gaya', 'Gaya'), ('muzaffarpur', 'Muzaffarpur'),
        ('bhagalpur', 'Bhagalpur'), ('darbhanga', 'Darbhanga'),
        ('purnia', 'Purnia'), ('arrah', 'Arrah'), ('begusarai', 'Begusarai'),
        ('katihar', 'Katihar'), ('munger', 'Munger'), ('chapra', 'Chapra'),
        ('hajipur', 'Hajipur'), ('samastipur', 'Samastipur'),
        ('sitamarhi', 'Sitamarhi'), ('siwan', 'Siwan'), ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, blank=True)
    school_name = models.CharField(max_length=200, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=20, unique=True, default=generate_referral_code)
    referred_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='referred_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.district}"

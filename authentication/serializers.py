from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserProfile


# ── Custom JWT payload ────────────────────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name'] = user.get_full_name()
        token['email'] = user.email
        token['role'] = getattr(user.profile, 'role', 'student')
        return token

    def validate(self, attrs):
        username_field = self.username_field
        login_value = attrs.get(username_field, '')

        # Allow login with email — resolve to actual username
        if '@' in login_value:
            try:
                user_obj = User.objects.get(email__iexact=login_value)
                attrs[username_field] = user_obj.username
            except User.DoesNotExist:
                pass

        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'name': self.user.get_full_name(),
            'role': getattr(self.user.profile, 'role', 'student'),
            'district': getattr(self.user.profile, 'district', ''),
            'phone': getattr(self.user.profile, 'phone', ''),
        }
        return data


# ── Register ──────────────────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, max_length=50)
    last_name = serializers.CharField(required=False, max_length=50, default='')
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True, max_length=15)
    district = serializers.CharField(required=True, max_length=50)
    school_name = serializers.CharField(required=False, max_length=200, default='')
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='student', required=False)
    referral_code = serializers.CharField(required=False, allow_blank=True, max_length=20, default='')
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'district',
                  'school_name', 'role', 'referral_code', 'password', 'password2')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_phone(self, value):
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) < 10 or len(digits) > 12:
            raise serializers.ValidationError("Enter a valid 10-digit phone number.")
        return digits

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_referral_code(self, value):
        if not value:
            return value
        from .models import UserProfile as UP
        if not UP.objects.filter(referral_code__iexact=value).exists():
            raise serializers.ValidationError('Invalid referral code.')
        return value.upper()

    def create(self, validated_data):
        from referral.services import validate_referral_code, process_referral_reward
        phone = validated_data.pop('phone')
        district = validated_data.pop('district')
        school_name = validated_data.pop('school_name', '')
        role = validated_data.pop('role', 'student')
        referral_code = validated_data.pop('referral_code', '')
        validated_data.pop('password2')

        username = validated_data['email'].split('@')[0]
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
        )

        referrer = None
        if referral_code:
            is_valid, _, referrer = validate_referral_code(referral_code, validated_data['email'])
            if not is_valid:
                referrer = None

        UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone,
            district=district,
            school_name=school_name,
            referred_by=referrer,
        )

        if referrer:
            process_referral_reward(referrer=referrer, referred_user=user)

        return user


# ── Admin / Staff Register ────────────────────────────────────────────────────
class AdminRegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, max_length=50)
    last_name = serializers.CharField(required=False, max_length=50, default='')
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, max_length=15, default='')
    district = serializers.CharField(required=False, max_length=50, default='')
    school_name = serializers.CharField(required=False, max_length=200, default='')
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True)
    is_staff = serializers.BooleanField(required=False, default=False)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'district',
                  'school_name', 'role', 'is_staff', 'password', 'password2')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_phone(self, value):
        if not value:
            return value
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) < 10 or len(digits) > 12:
            raise serializers.ValidationError("Enter a valid 10-digit phone number.")
        return digits

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone', '')
        district = validated_data.pop('district', '')
        school_name = validated_data.pop('school_name', '')
        role = validated_data.pop('role')
        is_staff = validated_data.pop('is_staff', False)
        validated_data.pop('password2')

        username = validated_data['email'].split('@')[0]
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            is_staff=is_staff,
        )
        UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone,
            district=district,
            school_name=school_name,
        )
        return user


# ── Profile ───────────────────────────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role', 'phone', 'district', 'school_name', 'profile_picture', 'is_verified', 'created_at')
        read_only_fields = ('is_verified', 'created_at')


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'name', 'profile', 'date_joined')
        read_only_fields = ('id', 'username', 'email', 'date_joined', 'profile__is_verified')

    def get_name(self, obj):
        return obj.get_full_name()

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        return instance


# ── Admin Panel — Full User Management ───────────────────────────────────────
class AdminUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role', 'phone', 'district', 'school_name', 'profile_picture', 'is_verified', 'created_at', 'updated_at')


class AdminUserDetailSerializer(serializers.ModelSerializer):
    profile = AdminUserProfileSerializer()
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'name',
                  'is_active', 'is_staff', 'date_joined', 'last_login', 'profile')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login')

    def get_name(self, obj):
        return obj.get_full_name()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, max_length=50)
    last_name = serializers.CharField(required=False, max_length=50)
    email = serializers.EmailField(required=False)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    phone = serializers.CharField(required=False, max_length=15)
    district = serializers.CharField(required=False, max_length=50)
    school_name = serializers.CharField(required=False, max_length=200)
    is_verified = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'is_active', 'is_staff',
                  'role', 'phone', 'district', 'school_name', 'is_verified')

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value.lower()

    def update(self, instance, validated_data):
        profile_fields = ('role', 'phone', 'district', 'school_name', 'is_verified')
        profile_data = {k: validated_data.pop(k) for k in profile_fields if k in validated_data}

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        return instance


class AdminResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs


# ── Change Password ───────────────────────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New passwords do not match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

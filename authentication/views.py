from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import UserProfile
from .permissions import IsAdmin
from .serializers import (
    RegisterSerializer,
    AdminRegisterSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer,
    AdminResetPasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserDetailSerializer,
    ChangePasswordSerializer,
)


class RegisterThrottle(AnonRateThrottle):
    rate = '5/hour'


_token_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
    }
)

_user_basic = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'email': openapi.Schema(type=openapi.TYPE_STRING),
        'username': openapi.Schema(type=openapi.TYPE_STRING),
        'role': openapi.Schema(type=openapi.TYPE_STRING, enum=[c[0] for c in UserProfile.ROLE_CHOICES]),
    }
)

_bearer_security = [{'Bearer': []}]
_admin_security = [{'Bearer': []}]
_role_enum = [c[0] for c in UserProfile.ROLE_CHOICES]


# ── Register ──────────────────────────────────────────────────────────────────
class RegisterView(generics.GenericAPIView):
    """POST /api/v1/auth/register/ — create student account"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [RegisterThrottle]

    @swagger_auto_schema(
        operation_id='auth_register',
        operation_summary='Register a new student account',
        operation_description=(
            'Publicly accessible. Creates a new user with role `student` by default. '
            'Returns JWT tokens on success. Rate limited to 5 requests/hour.'
        ),
        tags=['Auth'],
        security=[],
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description='Account created',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': _user_basic,
                        'tokens': _token_response,
                    }
                )
            ),
            400: 'Validation error',
            429: 'Rate limit exceeded — 5 registrations per hour',
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Account created successfully! Welcome to DasviClasses.',
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'username': user.username,
                'role': user.profile.role,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ — returns JWT access + refresh + user info"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_id='auth_login',
        operation_summary='Login with email or username',
        operation_description=(
            'Accepts username **or email** as the `username` field. '
            'Returns JWT access token, refresh token, and user info including role.'
        ),
        tags=['Auth'],
        security=[],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username or email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            }
        ),
        responses={
            200: openapi.Response(
                description='Login successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=_role_enum),
                                'district': openapi.Schema(type=openapi.TYPE_STRING),
                                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                    }
                )
            ),
            401: 'Invalid credentials',
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# ── Logout ────────────────────────────────────────────────────────────────────
class LogoutView(generics.GenericAPIView):
    """POST /api/v1/auth/logout/ — blacklist the refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    @swagger_auto_schema(
        operation_id='auth_logout',
        operation_summary='Logout — blacklist refresh token',
        operation_description='Blacklists the provided refresh token. Requires Bearer authentication.',
        tags=['Auth'],
        security=_bearer_security,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token to blacklist'),
            }
        ),
        responses={
            200: openapi.Response('Logged out', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            400: 'Invalid or missing refresh token',
            401: 'Authentication required',
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ───────────────────────────────────────────────────────────────────
class ProfileView(generics.GenericAPIView):
    """GET / PATCH /api/v1/auth/profile/ — view or update own profile"""
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_id='auth_profile_get',
        operation_summary='Get own profile',
        operation_description="Returns the authenticated user's full profile including role.",
        tags=['Auth'],
        security=_bearer_security,
        responses={200: UserDetailSerializer, 401: 'Authentication required'}
    )
    def get(self, request):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_id='auth_profile_update',
        operation_summary='Update own profile',
        operation_description='Partially update first_name, last_name, phone, district, school_name, role.',
        tags=['Auth'],
        security=_bearer_security,
        request_body=UserDetailSerializer,
        responses={200: UserDetailSerializer, 400: 'Validation error', 401: 'Authentication required'}
    )
    def patch(self, request):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Change Password ───────────────────────────────────────────────────────────
class ChangePasswordView(generics.GenericAPIView):
    """POST /api/v1/auth/change-password/ — change own password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_id='auth_change_password',
        operation_summary='Change own password',
        operation_description='Authenticated user changes their own password. Old password must be correct.',
        tags=['Auth'],
        security=_bearer_security,
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response('Password changed', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            400: 'Validation error or incorrect old password',
            401: 'Authentication required',
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

class AdminRegisterView(generics.GenericAPIView):
    """POST /api/v1/auth/admin/register/ — admin creates any role account"""
    serializer_class = AdminRegisterSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    @swagger_auto_schema(
        operation_id='admin_register_user',
        operation_summary='[Admin] Create user with any role',
        operation_description=(
            'Requires **admin** role JWT. Creates a new user with any role including '
            '`admin`, `teacher`, `school_teacher`, `school_principle`, `account`, `marketing`. '
            'Set `is_staff=true` to grant Django admin panel access.'
        ),
        tags=['Admin — Users'],
        security=_bearer_security,
        request_body=AdminRegisterSerializer,
        responses={
            201: openapi.Response(
                description='User created',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=_role_enum),
                                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        ),
                    }
                )
            ),
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin role required',
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': f'Account created successfully for {user.get_full_name() or user.username}.',
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'username': user.username,
                'role': user.profile.role,
                'is_staff': user.is_staff,
            },
        }, status=status.HTTP_201_CREATED)


class UserListView(generics.GenericAPIView):
    """GET /api/v1/auth/admin/users/?role=<role> — admin lists all users"""
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        role = self.request.query_params.get('role')
        qs = User.objects.select_related('profile').all().order_by('-date_joined')
        if role:
            qs = qs.filter(profile__role=role)
        return qs

    @swagger_auto_schema(
        operation_id='admin_list_users',
        operation_summary='[Admin] List all users',
        operation_description='Requires **admin** role JWT. Returns paginated list of all users. Filter by role using `?role=` query param.',
        tags=['Admin — Users'],
        security=_bearer_security,
        manual_parameters=[
            openapi.Parameter(
                'role', openapi.IN_QUERY,
                description='Filter by role',
                type=openapi.TYPE_STRING,
                enum=_role_enum,
                required=False,
            )
        ],
        responses={
            200: UserDetailSerializer(many=True),
            401: 'Authentication required',
            403: 'Admin role required',
        }
    )
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class AdminDashboardView(generics.GenericAPIView):
    """GET /api/v1/auth/admin/dashboard/ — overview stats"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = None

    @swagger_auto_schema(
        operation_id='admin_dashboard',
        operation_summary='[Admin] Dashboard stats',
        operation_description='Returns total user counts broken down by role, active/inactive, verified/unverified.',
        tags=['Admin — Panel'],
        security=_admin_security,
        responses={
            200: openapi.Response(
                description='Dashboard statistics',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'inactive_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'verified_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'by_role': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            401: 'Authentication required',
            403: 'Admin role required',
        }
    )
    def get(self, request):
        total = User.objects.count()
        active = User.objects.filter(is_active=True).count()
        verified = UserProfile.objects.filter(is_verified=True).count()
        by_role = dict(
            UserProfile.objects.values('role').annotate(count=Count('id')).values_list('role', 'count')
        )
        return Response({
            'total_users': total,
            'active_users': active,
            'inactive_users': total - active,
            'verified_users': verified,
            'by_role': by_role,
        })


class AdminUserDetailView(generics.GenericAPIView):
    """GET /api/v1/auth/admin/users/<pk>/ — get single user detail"""
    serializer_class = AdminUserDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return User.objects.select_related('profile').get(pk=pk)
        except User.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_id='admin_user_detail',
        operation_summary='[Admin] Get user detail',
        operation_description='Returns full profile, role, status and login info for a specific user.',
        tags=['Admin — Panel'],
        security=_admin_security,
        responses={
            200: AdminUserDetailSerializer,
            401: 'Authentication required',
            403: 'Admin role required',
            404: 'User not found',
        }
    )
    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class AdminUserUpdateView(generics.GenericAPIView):
    """PATCH /api/v1/auth/admin/users/<pk>/update/ — edit any user field"""
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return User.objects.select_related('profile').get(pk=pk)
        except User.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_id='admin_user_update',
        operation_summary='[Admin] Update user',
        operation_description=(
            'Partially update any user field: `first_name`, `last_name`, `email`, '
            '`is_active`, `is_staff`, `role`, `phone`, `district`, `school_name`, `is_verified`.'
        ),
        tags=['Admin — Panel'],
        security=_admin_security,
        request_body=AdminUserUpdateSerializer,
        responses={
            200: AdminUserDetailSerializer,
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin role required',
            404: 'User not found',
        }
    )
    def patch(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AdminUserDetailSerializer(user).data)


class AdminUserDeleteView(generics.GenericAPIView):
    """DELETE /api/v1/auth/admin/users/<pk>/delete/ — permanently delete user"""
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_id='admin_user_delete',
        operation_summary='[Admin] Delete user',
        operation_description='Permanently deletes the user and all associated profile data.',
        tags=['Admin — Panel'],
        security=_admin_security,
        responses={
            204: 'User deleted successfully',
            400: 'Cannot delete own account',
            401: 'Authentication required',
            403: 'Admin role required',
            404: 'User not found',
        }
    )
    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user == request.user:
            return Response({'error': 'You cannot delete your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response({'message': 'User deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class AdminToggleActiveView(generics.GenericAPIView):
    """POST /api/v1/auth/admin/users/<pk>/toggle-active/ — activate or deactivate"""
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_id='admin_toggle_active',
        operation_summary='[Admin] Toggle user active status',
        operation_description='Activates a deactivated user or deactivates an active user. Cannot deactivate yourself.',
        tags=['Admin — Panel'],
        security=_admin_security,
        responses={
            200: openapi.Response(
                description='Status toggled',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: 'Cannot deactivate own account',
            401: 'Authentication required',
            403: 'Admin role required',
            404: 'User not found',
        }
    )
    def post(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user == request.user:
            return Response({'error': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save()
        state = 'activated' if user.is_active else 'deactivated'
        return Response({'message': f'User {state} successfully.', 'is_active': user.is_active})


class AdminVerifyUserView(generics.GenericAPIView):
    """POST /api/v1/auth/admin/users/<pk>/verify/ — mark user as verified"""
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return UserProfile.objects.get(user__pk=pk)
        except UserProfile.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_id='admin_verify_user',
        operation_summary='[Admin] Verify user',
        operation_description='Marks the user profile as verified (`is_verified=true`).',
        tags=['Admin — Panel'],
        security=_admin_security,
        responses={
            200: openapi.Response(
                description='User verified',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            401: 'Authentication required',
            403: 'Admin role required',
            404: 'User not found',
        }
    )
    def post(self, request, pk):
        profile = self.get_object(pk)
        if not profile:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        profile.is_verified = True
        profile.save()
        return Response({'message': 'User verified successfully.', 'is_verified': True})


class AdminResetPasswordView(generics.GenericAPIView):
    """POST /api/v1/auth/admin/users/<pk>/reset-password/ — force reset a user's password"""
    serializer_class = AdminResetPasswordSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_id='admin_reset_password',
        operation_summary='[Admin] Reset user password',
        operation_description='Admin forcefully sets a new password for any user without requiring the old one.',
        tags=['Admin — Panel'],
        security=_admin_security,
        request_body=AdminResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description='Password reset',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin role required',
            404: 'User not found',
        }
    )
    def post(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': f'Password for {user.username} reset successfully.'})

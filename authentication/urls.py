from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .views import (
    RegisterView, LoginView, LogoutView, ProfileView, ChangePasswordView,
    AdminRegisterView, UserListView,
    AdminDashboardView, AdminUserDetailView, AdminUserUpdateView,
    AdminUserDeleteView, AdminToggleActiveView, AdminVerifyUserView, AdminResetPasswordView,
)


DecoratedTokenRefreshView = swagger_auto_schema(
    method='post',
    operation_id='auth_token_refresh',
    operation_summary='Refresh access token',
    operation_description='Provide a valid refresh token to receive a new access token.',
    tags=['Auth'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh'],
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Valid JWT refresh token'),
        }
    ),
    responses={
        200: openapi.Response(
            description='New access token issued',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'access': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        401: 'Refresh token invalid or expired',
    }
)(TokenRefreshView.as_view())

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('token/refresh/', DecoratedTokenRefreshView, name='token_refresh'),
    path('admin/register/', AdminRegisterView.as_view(), name='admin_register'),
    path('admin/users/', UserListView.as_view(), name='admin_user_list'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:pk>/update/', AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('admin/users/<int:pk>/delete/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
    path('admin/users/<int:pk>/toggle-active/', AdminToggleActiveView.as_view(), name='admin_toggle_active'),
    path('admin/users/<int:pk>/verify/', AdminVerifyUserView.as_view(), name='admin_verify_user'),
    path('admin/users/<int:pk>/reset-password/', AdminResetPasswordView.as_view(), name='admin_reset_password'),
]

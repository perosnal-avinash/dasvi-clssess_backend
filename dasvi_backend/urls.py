from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="DasviClasses API",
        default_version='v1',
        description="API documentation for DasviClasses - Bihar Board Class 10 Educational Platform",
        terms_of_service="https://dasviclasses.com/terms/",
        contact=openapi.Contact(email="api@dasviclasses.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/contact/', include('contact.urls')),
    path('api/v1/courses/', include('courses.urls')),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/referral/', include('referral.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

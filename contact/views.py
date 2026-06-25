from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ContactInquiry
from .serializers import ContactInquirySerializer, ContactInquiryAdminSerializer
from .throttles import ContactAnonThrottle, ContactUserThrottle
from .emails import send_contact_emails


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class ContactInquiryCreateView(generics.CreateAPIView):
    """Submit a contact inquiry. Rate limited to 5 per hour per IP."""
    serializer_class = ContactInquirySerializer
    permission_classes = [AllowAny]
    throttle_classes = [ContactAnonThrottle]

    @swagger_auto_schema(
        operation_summary="Submit contact inquiry",
        operation_description="Submit a contact/support inquiry. Rate limited to 5 per hour.",
        responses={
            201: openapi.Response("Inquiry submitted successfully", ContactInquirySerializer),
            400: "Validation error",
            429: "Rate limit exceeded",
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inquiry = serializer.save(ip_address=get_client_ip(request))
        send_contact_emails(inquiry)
        return Response(
            {
                "success": True,
                "message": "Your inquiry has been submitted successfully. We will contact you within 24 hours.",
                "reference_id": f"DC-{inquiry.id:06d}",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )


class ContactInquiryListView(generics.ListAPIView):
    """Admin: List all contact inquiries with filtering."""
    queryset = ContactInquiry.objects.all()
    serializer_class = ContactInquiryAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'subject']
    search_fields = ['name', 'email', 'phone', 'message']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    @swagger_auto_schema(operation_summary="List all contact inquiries (Admin only)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ContactInquiryDetailView(generics.RetrieveUpdateAPIView):
    """Admin: Retrieve or update a contact inquiry."""
    queryset = ContactInquiry.objects.all()
    serializer_class = ContactInquiryAdminSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(operation_summary="Get contact inquiry detail (Admin only)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update contact inquiry status (Admin only)")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

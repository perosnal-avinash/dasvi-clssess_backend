from django.urls import path
from .views import ContactInquiryCreateView, ContactInquiryListView, ContactInquiryDetailView

urlpatterns = [
    path('', ContactInquiryCreateView.as_view(), name='contact-create'),
    path('list/', ContactInquiryListView.as_view(), name='contact-list'),
    path('<int:pk>/', ContactInquiryDetailView.as_view(), name='contact-detail'),
]

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_contact_emails(inquiry):
    """Send confirmation email to student and notification to admin."""
    # Email to admin
    try:
        admin_subject = f"[DasviClasses] New Contact Inquiry: {inquiry.get_subject_display()}"
        admin_body = f"""
New contact inquiry received on DasviClasses:

Name: {inquiry.name}
Email: {inquiry.email}
Phone: {inquiry.phone}
Subject: {inquiry.get_subject_display()}
Message:
{inquiry.message}

Submitted at: {inquiry.created_at.strftime('%d %B %Y, %I:%M %p IST')}
IP Address: {inquiry.ip_address}

Please login to admin panel to review and respond.
Admin Panel: http://localhost:8000/admin/contact/contactinquiry/{inquiry.id}/change/
"""
        send_mail(
            subject=admin_subject,
            message=admin_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )
    except Exception:
        pass

    # Confirmation email to student
    try:
        student_subject = "Thank you for contacting DasviClasses!"
        student_body = f"""
Dear {inquiry.name},

Thank you for reaching out to DasviClasses!

We have received your inquiry regarding "{inquiry.get_subject_display()}" and our team will get back to you within 24 hours.

Your Inquiry Details:
- Subject: {inquiry.get_subject_display()}
- Message: {inquiry.message[:200]}{'...' if len(inquiry.message) > 200 else ''}
- Reference ID: DC-{inquiry.id:06d}

For urgent queries, you can also reach us on WhatsApp: +91-XXXXXXXXXX

Best Regards,
DasviClasses Team
Bihar Board Class 10 Excellence
Website: https://dasviclasses.com
"""
        send_mail(
            subject=student_subject,
            message=student_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email],
            fail_silently=True,
        )
    except Exception:
        pass

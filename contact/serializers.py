import re
from rest_framework import serializers
from .models import ContactInquiry


class ContactInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInquiry
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Name must contain only letters and spaces.")
        return value

    def validate_phone(self, value):
        value = re.sub(r'\s+', '', value)
        if not re.match(r'^(\+91)?[6-9]\d{9}$', value):
            raise serializers.ValidationError("Enter a valid Indian mobile number.")
        return value

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters.")
        spam_keywords = ['casino', 'lottery', 'win money', 'click here', 'free money']
        if any(kw in value.lower() for kw in spam_keywords):
            raise serializers.ValidationError("Message contains prohibited content.")
        return value


class ContactInquiryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInquiry
        fields = '__all__'

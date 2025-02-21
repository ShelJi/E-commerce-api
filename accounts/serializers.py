from rest_framework import serializers

from accounts.models import (UserManagementModel,
                             CustomerModel,
                             OTPVerifyModel,
                             SellerModel,
                             DeliveryBoyModel)
from accounts.utils import (send_otp,
                            generate_first_otp)

from datetime import timedelta
from django.utils import timezone

import random


class UserManagementSignUpSerializer(serializers.ModelSerializer):
    """Create Custom User."""

    class Meta:
        model = UserManagementModel
        fields = ["phone_no", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        """
        Create and return a new UserManagementModel instance
        or return the existing user if already created.
        """
        user = UserManagementModel.objects.create(
            phone_no=validated_data["phone_no"],
            username=validated_data["username"]
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomerSignUpSerializer(serializers.ModelSerializer):
    """Create new customer and send OTP."""
    user = UserManagementSignUpSerializer()

    class Meta:
        model = CustomerModel
        fields = ["user"]

    def create(self, validated_data):
        """Create Customer and send OTP."""
        user_data = validated_data.pop("user")
        user = UserManagementSignUpSerializer().create(user_data)

        customer, created = CustomerModel.objects.get_or_create(user=user, defaults=validated_data)

        if created:
            generate_first_otp(user)

        return customer


class SellerSignUpSerializer(serializers.ModelSerializer):
    """Serialize data required for Seller signup"""
    user = UserManagementSignUpSerializer()

    class Meta:
        model = SellerModel
        exclude = ["is_active", "is_otp", "clo_coin", "seller_rank", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create Seller and send OTP."""
        user_data = validated_data.pop("user")
        user = UserManagementSignUpSerializer().create(user_data)

        seller, created = SellerModel.objects.get_or_create(user=user, defaults=validated_data)

        if created:
            generate_first_otp(user)

        return seller


class DeliveryBoySignUpSerializer(serializers.ModelSerializer):
    """Serialize data required for Delivery Boy signup"""
    user = UserManagementSignUpSerializer()

    class Meta:
        model = DeliveryBoyModel
        fields = ["license_no", "file_license", "user"]

    def create(self, validated_data):
        """Create Delivery Boy and send OTP."""
        user_data = validated_data.pop("user")
        user = UserManagementSignUpSerializer().create(user_data)

        delivery_boy, created = DeliveryBoyModel.objects.get_or_create(user=user, defaults=validated_data)

        if created:
            generate_first_otp(user)

        return delivery_boy


class OTPValidateSerializer(serializers.Serializer):
    """Validate OTP requests."""
    otp = serializers.CharField(max_length=6)
    username = serializers.CharField(max_length=150)
    is_seller = serializers.BooleanField(default=False)
    is_delivery_boy = serializers.BooleanField(default=False)

    def validate(self, data):
        """Validates OTP."""
        otp = data.get("otp")
        username = data.get("username")

        try:
            otp_entry = OTPVerifyModel.objects.get(user__username=username)
        except OTPVerifyModel.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid username name."})

        if otp_entry.otp_expiry < timezone.localtime(timezone.now()):
            raise serializers.ValidationError({"otp": "OTP has expired. Please request a new one."})

        if otp_entry.otp != str(otp):
            raise serializers.ValidationError({"otp": "OTP does not match."})

        return data


class OTPResendSerializer(serializers.Serializer):
    """Verify OTP resend."""
    username = serializers.CharField(max_length=150)

    def validate(self, data):
        """Validates if OTP can be resent."""
        username = data.get("username")

        try:
            user = UserManagementModel.objects.get(username=username)
                
        except UserManagementModel.DoesNotExist:
            raise serializers.ValidationError({"username": "User does not exist."})

        otp, created = OTPVerifyModel.objects.get_or_create(
            user=user,
            defaults={"otp": random.randint(100000, 999999), 
                      "otp_expiry": timezone.localtime(timezone.now()) + timedelta(minutes=10)}
        )

        if not created:
            if otp.otp_max_out and otp.otp_max_out > timezone.localtime(timezone.now()):
                raise serializers.ValidationError({"otp": f"Maximum OTP request limit reached. Try again later."})

            if otp.otp_expiry > timezone.localtime(timezone.now()):
                raise serializers.ValidationError({"otp": f"Already requested OTP! Try after 10 minutes."})

        send_otp(user.phone_no, otp.otp)

        return {"user": user}


class LoginSerializer(serializers.Serializer):
    """Base Login Serializer for all user roles."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

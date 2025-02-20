from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import (UserManagementModel,
                             CustomerModel,
                             OTPVerifyModel,
                             SellerModel,
                             DeliveryBoyModel)
from accounts.utils import (send_otp,
                            generate_otp)

from cloviogo_main.settings import OTP_MAX_TRY
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate


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
        user, created = UserManagementModel.objects.get_or_create(
            phone_no=validated_data["phone_no"],
            defaults={"username": validated_data["username"]}
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
            generate_otp(user)

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
            generate_otp(user)

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
            generate_otp(user)

        return delivery_boy


class OTPValidateSerializer(serializers.Serializer):
    """Validate OTP requests."""
    otp = serializers.CharField(max_length=4)
    phone_no = serializers.CharField(max_length=10)
    is_seller = serializers.BooleanField(default=False)
    is_delivery_boy = serializers.BooleanField(default=False)

    def validate(self, data):
        """Validates OTP."""
        otp = data.get("otp")
        phone_no = data.get("phone_no")

        try:
            otp_entry = OTPVerifyModel.objects.get(user__phone_no=phone_no)
        except OTPVerifyModel.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid phone number."})

        if otp_entry.otp_expiry < timezone.now():
            raise serializers.ValidationError({"otp": "OTP has expired. Please request a new one."})

        if otp_entry.otp != str(otp):
            raise serializers.ValidationError({"otp": "OTP does not match."})

        return data


class OTPResendSerializer(serializers.Serializer):
    """Verify OTP resend."""
    phone_no = serializers.CharField(max_length=15)

    def validate(self, data):
        """Validates if OTP can be resent."""
        phone_no = data.get("phone_no")

        try:
            user = UserManagementModel.objects.get(phone_no=phone_no)
        except UserManagementModel.DoesNotExist:
            raise serializers.ValidationError({"phone_no": "User with this phone number does not exist."})

        otp, created = OTPVerifyModel.objects.get_or_create(
            user=user,
            defaults={"otp": random.randint(10000, 99999), "otp_expiry": timezone.now() + timedelta(minutes=10)}
        )

        if not created:
            if otp.otp_expiry > timezone.now():
                raise serializers.ValidationError({"otp": f"Already requested OTP! Try after {otp.otp_expiry.strftime('%Y-%m-%d %H:%M:%S')}."})

            if otp.otp_max_out and otp.otp_max_out > timezone.now():
                raise serializers.ValidationError({"otp": f"Maximum OTP request limit reached. Try after {otp.otp_max_out.strftime('%Y-%m-%d %H:%M:%S')}."})

            otp.otp = random.randint(10000, 99999)
            otp.otp_expiry = timezone.now() + timedelta(minutes=10)
            otp.otp_max_try = OTP_MAX_TRY - 1
            otp.save()

        send_otp(user.phone_no, otp.otp)

        return {"user": user}


class LoginSerializer(serializers.Serializer):
    """Base Login Serializer for all user roles."""
    phone_no = serializers.CharField(max_length=10, required=False)
    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validate user credentials."""
        phone_no = data.get("phone_no")
        username = data.get("username")
        password = data.get("password")

        if not (phone_no or username):
            raise serializers.ValidationError({"error": "Either phone number or username is required."})

        user = None
        if phone_no:
            user = authenticate(phone_no=phone_no, password=password)
        elif username:
            user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError({"error": "Invalid phone number, username, or password."})

        if not user.is_active:
            raise serializers.ValidationError({"error": "Account is inactive. Please verify your OTP."})

        tokens = RefreshToken.for_user(user)
        return {
            "refresh": str(tokens),
            "access": str(tokens.access_token),
            "user_id": user.id,
            "username": user.username
        }
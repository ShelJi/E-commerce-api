from rest_framework import serializers

from accounts.models import (UserManagementModel,
                             CustomerModel,
                             OTPVerifyModel,
                             SellerModel,
                             DeliveryBoyModel)
from accounts.utils import (send_otp,
                            generate_first_otp,
                            create_otp_model_first)

from datetime import timedelta
from django.utils import timezone

import random

from django.contrib.auth import get_user_model

User = get_user_model()


class UserManagementSignUpSerializer(serializers.ModelSerializer):
    """Create Custom User."""

    class Meta:
        model = User
        fields = ["phone_no", "username", "password"]
        extra_kwargs = {"password": {"write_only": True, 'min_length': 5}}

    def create(self, validated_data): 
        """
        Create and return a new UserManagementModel instance
        or return the existing user if already created.
        """
        user = User.objects.create(
            phone_no=validated_data["phone_no"],
            username=validated_data["username"]
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomerSignUpSerializer(serializers.ModelSerializer):
    """Create send OTP and create new customer."""
    user = UserManagementSignUpSerializer()

    class Meta:
        model = CustomerModel
        fields = ["user"]

    def create(self, validated_data):
        """Send OTP and create CustomerModel."""
        user_data = validated_data.pop("user")

        ######################## Need to add this to verify if the user already exists or registered with this phone_no
        # customer = CustomerModel.objects.filter(user__phone_no=user_data["phone_no"]).first()

        # if customer:
        #     if not customer.user.is_active:
        #         raise serializers.ValidationError("User with this mobile number exists but is not verified. Please verify OTP.")
        #     raise serializers.ValidationError("User with this mobile number already exists. Please try logging in.")
            
        otp = generate_first_otp(user_data["phone_no"])
        user = UserManagementSignUpSerializer().create(user_data)
        create_otp_model_first(user, otp)
        customer = CustomerModel.objects.create(user=user, **validated_data)
        return customer


class SellerSignUpSerializer(serializers.ModelSerializer):
    """Serialize data required for Seller signup"""
    user = UserManagementSignUpSerializer()

    class Meta:
        model = SellerModel
        exclude = ["is_active", "is_otp", "clo_coin", "seller_rank", "created_at", "updated_at"]

    def create(self, validated_data):
        """Send OTP and create SellerModel."""
        user_data = validated_data.pop("user")
        otp = generate_first_otp(user_data["phone_no"])
        user = UserManagementSignUpSerializer().create(user_data)
        create_otp_model_first(user, otp)
        seller = SellerModel.objects.create(user=user, **validated_data)
        return seller


class DeliveryBoySignUpSerializer(serializers.ModelSerializer):
    """Serialize data required for Delivery Boy signup"""
    user = UserManagementSignUpSerializer()

    class Meta:
        model = DeliveryBoyModel
        fields = ["license_no", "file_license", "user"]

    def create(self, validated_data):
        """Send OTP and create DeliveryBoyModel."""
        user_data = validated_data.pop("user")
        otp = generate_first_otp(user_data["phone_no"])
        user = UserManagementSignUpSerializer().create(user_data)
        create_otp_model_first(user, otp)
        deliveryboy = DeliveryBoyModel.objects.create(user=user, **validated_data)
        return deliveryboy


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
            user = User.objects.get(username=username)
                
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User does not exist."})

        try:
            otp = OTPVerifyModel.objects.get(user=user)
                
        except OTPVerifyModel.DoesNotExist:
            otp = None

        if otp is not None:
            if otp.otp_max_out and otp.otp_max_out > timezone.localtime(timezone.now()):
                raise serializers.ValidationError({"otp": f"Maximum OTP request limit reached. Try again later."})

            if otp.otp_expiry > timezone.localtime(timezone.now()):
                raise serializers.ValidationError({"otp": f"Already requested OTP! Try after 10 minutes."})

        return {"user": user}


class LoginSerializer(serializers.Serializer):
    """Base Login Serializer for all user roles."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """Login response visualise for Swagger UI."""
    refresh = serializers.CharField()
    access = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()


"""
Views handling accounts and OTP verifications.
"""

"""is_otp not added, imagemodel, filemodel"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView

from accounts.serializers import (CustomerSignUpSerializer,
                                  OTPValidateSerializer,
                                  OTPResendSerializer,
                                  SellerSignUpSerializer,
                                  DeliveryBoySignUpSerializer,
                                  LoginSerializer)
from accounts.models import (CustomerModel,
                             UserManagementModel,
                             OTPVerifyModel,
                             SellerModel,
                             DeliveryBoyModel)
from accounts.utils import send_otp
from django.utils import timezone

import random
from datetime import timedelta


class CustomerSignUpView(CreateAPIView):
    """
    Requires username, password, phone number to create a customer as inactive.
    """
    serializer_class = CustomerSignUpSerializer

    def get_queryset(self):
        return CustomerModel.objects.filter(user__is_active=False)


class SellerSignUpView(CreateAPIView):
    """
    Requires username, password, phone number to create a seller as inactive.
    """
    serializer_class = SellerSignUpSerializer

    def get_queryset(self):
        return SellerModel.objects.filter(user__is_active=False)


class DeliveryBoySignUpView(CreateAPIView):
    """
    Requires username, password, phone number to create a user as inactive.
    """
    serializer_class = DeliveryBoySignUpSerializer

    def get_queryset(self):
        return DeliveryBoyModel.objects.filter(user__is_active=False)


class OTPValidateView(APIView):
    """View for validating OTP for Customer, Seller, and Delivery Boy."""

    def post(self, request):
        """Verify OTP and activate user for all roles they belong to."""
        serializer = OTPValidateSerializer(data=request.data)

        if serializer.is_valid():
            phone_no = serializer.validated_data["phone_no"]
            is_seller = serializer.validated_data["is_seller"]
            is_delivery_boy = serializer.validated_data["is_delivery_boy"]

            user = UserManagementModel.objects.get(phone_no=phone_no)
            user.is_active = True
            user.save()

            OTPVerifyModel.objects.filter(user=user).delete()

            if is_seller:
                seller = SellerModel.objects.get(user = user)
                seller.is_otp = True
                seller.save()
                return Response(
                    {"message": "OTP matched. Seller OTP verified successfully!"},
                    status=status.HTTP_200_OK
                )

            if is_delivery_boy:
                delivery_boy = DeliveryBoyModel.objects.get(user = user)
                delivery_boy.is_otp = True
                delivery_boy.save()
                return Response(
                    {"message": "OTP matched. Delivery boy OTP verified successfully!"},
                    status=status.HTTP_200_OK
                )
                
            return Response(
                {"message": "OTP matched. Account activated successfully!"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OTPResendView(APIView):
    """View for OTP resend request for Customer, Seller, and Delivery Boy."""

    def post(self, request):
        """Resend OTP if applicable."""
        serializer = OTPResendSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            otp_entry, created = OTPVerifyModel.objects.get_or_create(
                user=user,
                defaults={
                    "otp": random.randint(10000, 99999),
                    "otp_expiry": timezone.now() + timedelta(minutes=10),
                    "otp_max_try": OTPVerifyModel._meta.get_field("otp_max_try").default
                }
            )

            # Prevent resend if max tries are exhausted
            if not created and otp_entry.otp_max_try <= 0:
                return Response(
                    {"message": f"Maximum OTP attempts reached. Try after {otp_entry.otp_max_out.strftime('%Y-%m-%d %H:%M:%S')}."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Send OTP
            otp_entry.otp = random.randint(10000, 99999)
            otp_entry.otp_expiry = timezone.now() + timedelta(minutes=10)
            otp_entry.otp_max_try -= 1

            if otp_entry.otp_max_try <= 0:
                otp_entry.otp_max_out = timezone.now() + timedelta(minutes=60)

            otp_entry.save()
            otp_sent = send_otp(user.phone_no, otp_entry.otp)

            if not otp_sent:
                return Response({"message": "Failed to send OTP. Please try again later."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "OTP resent successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerLoginView(APIView):
    """Login view for customers."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            if not CustomerModel.objects.filter(user__id=user["user_id"]).exists():
                return Response({"error": "User is not a customer."}, status=status.HTTP_403_FORBIDDEN)
            return Response(user, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerLoginView(APIView):
    """Login view for sellers."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            if not SellerModel.objects.filter(user__id=user["user_id"]).exists():
                return Response({"error": "User is not a seller."}, status=status.HTTP_403_FORBIDDEN)
            return Response(user, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeliveryBoyLoginView(APIView):
    """Login view for delivery boys."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            if not DeliveryBoyModel.objects.filter(user__id=user["user_id"]).exists():
                return Response({"error": "User is not a delivery boy."}, status=status.HTTP_403_FORBIDDEN)
            return Response(user, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

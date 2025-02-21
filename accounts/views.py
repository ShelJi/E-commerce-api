"""
Views handling accounts and OTP verifications.
"""

"""eraser-is_otp not added, imagemodel, filemodel"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

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
from django.contrib.auth import authenticate

from cloviogo_main.settings import OTP_MAX_TRY

import random
from datetime import timedelta


class CustomerSignUpView(CreateAPIView):
    """
    Requires username, password, phone number to create a customer account as inactive.
    Use validated password and phonenumber.
    """
    serializer_class = CustomerSignUpSerializer


class SellerSignUpView(CreateAPIView):
    """
    Requires username, password, phone number to create a seller account as inactive.
    Use validated password and phonenumber.
    """
    serializer_class = SellerSignUpSerializer


class DeliveryBoySignUpView(CreateAPIView):
    """
    Requires username, password, phone number to create delivery boy account as inactive.
    Use validated password and phonenumber.
    """
    serializer_class = DeliveryBoySignUpSerializer


class OTPValidateView(APIView):
    """
    View for validating OTP for Customer, Seller, and Delivery Boy.
    Requires Username and OTP.
    """

    def post(self, request):
        """Verify OTP and activate user for all roles they belong to."""
        serializer = OTPValidateSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data["username"]
            is_seller = serializer.validated_data["is_seller"]
            is_delivery_boy = serializer.validated_data["is_delivery_boy"]

            user = UserManagementModel.objects.get(username=username)
            user.is_active = True
            user.save()

            OTPVerifyModel.objects.filter(user=user).delete()

            if is_seller and SellerModel.objects.filter(user=user).exists():
                seller = SellerModel.objects.get(user = user)
                seller.is_otp = True
                seller.save()
                return Response(
                    {"message": "OTP matched. Seller OTP verified successfully!"},
                    status=status.HTTP_200_OK
                )

            if is_delivery_boy and DeliveryBoyModel.objects.filter(user=user).exists():
                delivery_boy = DeliveryBoyModel.objects.get(user = user)
                delivery_boy.is_otp = True
                delivery_boy.save()
                return Response(
                    {"message": "OTP matched. Delivery boy OTP verified successfully!"},
                    status=status.HTTP_200_OK
                )

            if CustomerModel.objects.filter(user=user).exists():
                customer = CustomerModel.objects.get(user = user)
                customer.is_otp = True
                customer.is_active = True
                customer.save()
                return Response(
                    {"message": "OTP matched. Customer is verified and activated successfully!"},
                    status=status.HTTP_200_OK
                )
                
            return Response(
                {"message": "OTP matched. User created but Account not activated."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OTPResendView(APIView):
    """
    View for OTP resend request for Customer, Seller, and Delivery Boy.
    Username is required.
    """

    def post(self, request):
        """Resend OTP if applicable."""
        serializer = OTPResendSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            otp_entry, created = OTPVerifyModel.objects.get_or_create(
                user=user,
                defaults={
                    "otp": random.randint(100000, 999999),
                    "otp_expiry": timezone.localtime(timezone.now()) + timedelta(minutes=10)
                }
            )

            if otp_entry.otp_max_out is not None:
                if otp_entry.otp_max_out < timezone.localtime(timezone.now()) and int(otp_entry.otp_max_try) <= 0:
                        otp_entry.otp_max_try = OTP_MAX_TRY

            otp_entry.otp = random.randint(100000, 999999)
            otp_entry.otp_expiry = timezone.localtime(timezone.now()) + timedelta(minutes=10)
            otp_entry.otp_max_try = int(otp_entry.otp_max_try) - 1

            if int(otp_entry.otp_max_try) <= 0:
                otp_entry.otp_max_out = timezone.localtime(timezone.now()) + timedelta(hours=1)

            otp_entry.save()
            otp_sent = send_otp(user.phone_no, otp_entry.otp)

            if not otp_sent:
                return Response({"message": "Failed to send OTP. Please try again later."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "OTP resent successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    """
    Login any user.
    login_user -> customer, seller or deliveryboy
    username and password is required.
    """

    def post(self, request, login_user):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data["username"].lower()
            password = serializer.validated_data["password"]

            user = authenticate(username=username, password=password)

            if not user:
                return Response({"error": "Invalid Username or Password."}, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                return Response({"error": "Account is inactive."}, status=status.HTTP_403_FORBIDDEN)

            # Validate user role
            if login_user == "customer":
                if not CustomerModel.objects.filter(user=user).exists():
                    return Response({"error": "Customer account not found."}, status=status.HTTP_404_NOT_FOUND)
                
                customer = CustomerModel.objects.get(user=user)
                if not customer.is_active:
                    return Response({"error": "Customer account not activated."}, status=status.HTTP_403_FORBIDDEN)

            elif login_user == "seller":
                if not SellerModel.objects.filter(user=user).exists():
                    return Response({"error": "Seller account not found."}, status=status.HTTP_404_NOT_FOUND)

                seller = SellerModel.objects.get(user=user)
                if not seller.is_active:
                    return Response({"error": "Seller account not activated."}, status=status.HTTP_403_FORBIDDEN)

            elif login_user == "deliveryboy":
                if not DeliveryBoyModel.objects.filter(user=user).exists():
                    return Response({"error": "Delivery Boy account not found."}, status=status.HTTP_404_NOT_FOUND)

                deliveryboy = DeliveryBoyModel.objects.get(user=user)
                if not deliveryboy.is_active:
                    return Response({"error": "Delivery Boy account not activated."}, status=status.HTTP_403_FORBIDDEN)

            else:
                return Response({"error": "Invalid user role."}, status=status.HTTP_400_BAD_REQUEST)

            # Generate JWT Tokens
            tokens = RefreshToken.for_user(user)

            return Response(
                {
                    "refresh": str(tokens),
                    "access": str(tokens.access_token),
                    "user_id": user.id,
                    "username": user.username
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

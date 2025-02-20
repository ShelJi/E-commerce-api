"""
URL mappings for the accounts.
"""
from django.urls import path
from accounts.views import (CustomerSignUpView,
                            OTPValidateView,
                            OTPResendView,
                            SellerSignUpView,
                            DeliveryBoySignUpView,
                            CustomerLoginView,
                            SellerLoginView,
                            DeliveryBoyLoginView)


app_name = "accounts"

urlpatterns = [
    path('signup/customer/', CustomerSignUpView.as_view(), name="customer_signup"),
    path('signup/seller/', SellerSignUpView.as_view(), name="seller_signup"),
    path('signup/deliveryboy/', DeliveryBoySignUpView.as_view(), name="deliveryboy_signup"),
    path('user/otp/validate/', OTPValidateView.as_view(), name="otp_validate"),
    path('user/otp/resend/', OTPResendView.as_view(), name="otp_resend"),

    path('login/customer/', CustomerLoginView.as_view(), name="customer_login"),
    path('login/seller/', SellerLoginView.as_view(), name="seller_login"),
    path('login/deliveryboy/', DeliveryBoyLoginView.as_view(), name="deliveryboy_login"),
]

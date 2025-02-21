from django.contrib import admin
from accounts.models import (UserManagementModel,
                             CustomerModel,
                             SellerModel,
                             DeliveryBoyModel,
                             OTPVerifyModel)


admin.site.register(UserManagementModel)
admin.site.register(CustomerModel)
admin.site.register(SellerModel)
admin.site.register(DeliveryBoyModel)
admin.site.register(OTPVerifyModel)
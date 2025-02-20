from django.contrib import admin
from accounts.models import (UserManagementModel,
                             CustomerModel,
                             SellerModel,
                             DeliveryBoyModel)


admin.site.register(UserManagementModel)
admin.site.register(CustomerModel)
admin.site.register(SellerModel)
admin.site.register(DeliveryBoyModel)
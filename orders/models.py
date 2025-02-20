from django.db import models
from core.globalchoices import ORDER_STATUS_CHOICES
from core.models import ImageModel
from accounts.models import CustomerModel
from products.models import ProductModel


class OrderModel(models.Model):
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    customer = models.ForeignKey(CustomerModel, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LatestDealModel(models.Model):
    image = models.ForeignKey(ImageModel, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.SET_NULL, null=True, blank=True)
    page_slug = models.SlugField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

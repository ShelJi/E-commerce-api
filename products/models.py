from django.db import models
from core.globalchoices import (PRODUCTS_CHOICES,
                                COLOR_CHOICES,
                                RATING_CHOICES)
from core.models import ImageModel, ColorModel
from accounts.models import (SellerModel,
                             CustomerModel)


class ProductModel(models.Model):
    seller = models.ForeignKey(SellerModel, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    product_category = models.CharField(max_length=50, choices=PRODUCTS_CHOICES)
    color_available = models.ForeignKey(ColorModel, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES)
    trend_order = models.IntegerField()
    actual_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    stocks = models.PositiveIntegerField()
    image = models.ForeignKey(ImageModel, on_delete=models.CASCADE)
    discount_percentage = models.PositiveIntegerField(default=0)
    is_return_policy = models.BooleanField(default=False)
    return_before = models.CharField(max_length=255)
    delivered_within = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name


class ReviewModel(models.Model):
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.CharField(max_length=10, choices=RATING_CHOICES)
    customer = models.ForeignKey(CustomerModel, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



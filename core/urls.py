from django.urls import path
from core.views import *


app_name = "catalog"

urlpatterns = [
    path('', CatalogHomeView.as_view(), name='catalog'),
]

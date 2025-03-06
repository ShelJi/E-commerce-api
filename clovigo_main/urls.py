from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# from drf_spectacular_sidecar.views import SpectacularSwaggerView, SpectacularRedocView, SpectacularRapidocView



urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', include("core.urls")), 
    path('api/accounts/', include("accounts.urls")),
    # path('cart', include("cart.urls")),
    # path('orders', include("orders.urls")),
    # path('products', include("products.urls")),


    # YOUR PATTERNS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/catalog/main/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/catalog/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

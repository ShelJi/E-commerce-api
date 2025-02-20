from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured
from drf_spectacular.utils import extend_schema


class CatalogHomeView(APIView):
    """
    API endpoint to provide the catalog details.
    Returns catalog main url.
    """

    @extend_schema(
        summary="Catalog main redirector",
        description="Catalog to redirect based on sections",
        request=None,
    )

    def get(self, request):
        """
        Handles GET requests to return API documentation link dynamically.
        """
        try:
            current_site = get_current_site(request).domain
            
            swagger_url = reverse("swagger-ui")
            catalog_link = f"{request.scheme}://{current_site}{swagger_url}"

            response_data = {
                "message": "Welcome to CloviGo API",
                "catalog": catalog_link,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except ImproperlyConfigured:
            return Response(
                {"error": "Site configuration is missing or incorrect."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

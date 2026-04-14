from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

# Le router génère automatiquement les URLs pour GET, POST, etc. [cite: 18, 159]
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    # Cela créera l'URL : /api/orders/ [cite: 71, 73]
    path('api/', include(router.urls)),
]
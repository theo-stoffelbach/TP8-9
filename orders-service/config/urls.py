from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Utilise la syntaxe standard pour l'admin
    path('admin/', admin.site.urls),

    # On branche les URLs de l'application 'orders'
    path('', include('orders.urls')),
]
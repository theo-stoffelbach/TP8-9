from django.urls import path

from . import api_views, views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/customers/", api_views.customer_list, name="customer-list"),
    path("api/customers/<int:pk>/", api_views.customer_detail, name="customer-detail"),
    path("api/customers/<int:pk>/addresses/", api_views.customer_addresses, name="customer-addresses"),
    path("api/customers/<int:pk>/addresses/<int:addr_pk>/", api_views.address_detail, name="address-detail"),
]

from django.contrib import admin

from .models import Address, Customer


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "email", "phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["email", "last_name", "first_name"]
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "street", "city", "postal_code", "country", "is_default"]
    list_filter = ["country", "is_default"]

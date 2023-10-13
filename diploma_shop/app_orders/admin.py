from django.contrib import admin
from .models import Order, Basket, BasketItem, PaymentCard
from typing import Type


class OrderAdmin(admin.ModelAdmin):
    list_display: list[str] = [
        'id',
        'createdAt',
        'status',
        'deliveryType',
        'paymentType',
        'totalCost',
        'city',
        'address'
    ]
    list_display_links: list[str] = list_display
    search_fields: list[str] = ['id']
    ordering: list[str] = ['id']


class BasketAdmin(admin.ModelAdmin):
    list_display: list[str] = [
        'id',
        'user',
    ]
    list_display_links: list[str] = list_display
    search_fields: list[str] = ['id']
    ordering: list[str] = ['id']


class BasketItemAdmin(admin.ModelAdmin):
    list_display: list[str] = [
        'id',
        'basket',
        'count',
        'product'
    ]
    list_display_links: list[str] = list_display
    search_fields: list[str] = ['id']
    ordering: list[str] = ['id']


class PaymentCardAdmin(admin.ModelAdmin):
    list_display: list[str] = [
        'id',
        'owner',
        'number',
        'name',
        'month',
        'year',
        'code'
    ]
    list_display_links: list[str] = list_display
    search_fields: list[str] = ['id']
    ordering: list[str] = ['id']


admin.site.register(Order, OrderAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(BasketItem, BasketItemAdmin)
admin.site.register(PaymentCard, PaymentCardAdmin)

admin.site.site_title = 'Админ-панель приложения app_orders'
admin.site.site_header = 'Админ-панель приложения app_orders'

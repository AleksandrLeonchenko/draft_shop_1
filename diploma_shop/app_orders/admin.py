
from django.contrib import admin
from .models import *


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'createdAt',
        'status',
        'deliveryType',
        'paymentType',
        'totalCost',
        'city',
        'address'
    ]
    list_display_links = [
        'id',
        'createdAt',
        'status',
        'deliveryType',
        'paymentType',
        'totalCost',
        'city',
        'address'
    ]
    search_fields = ['id']
    ordering = ['id']


class BasketAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
    ]
    list_display_links = [
        'id',
        'user',
    ]
    search_fields = ['id']
    ordering = ['id']


class BasketItemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'basket',
        'count',
        'product'
    ]
    list_display_links = [
        'id',
        'basket',
        'count',
        'product'
    ]
    search_fields = ['id']
    ordering = ['id']


class PaymentCardAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'owner',
        'number',
        'name',
        'month',
        'year',
        'code'
    ]
    list_display_links = [
        'id',
        'owner',
        'number',
        'name',
        'month',
        'year',
        'code'
    ]
    search_fields = ['id']
    ordering = ['id']


admin.site.register(Order, OrderAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(BasketItem, BasketItemAdmin)
admin.site.register(PaymentCard, PaymentCardAdmin)

admin.site.site_title = 'Админ-панель приложения app_orders'
admin.site.site_header = 'Админ-панель приложения app_orders'

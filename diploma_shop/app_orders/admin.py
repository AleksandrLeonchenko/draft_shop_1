# from io import TextIOWrapper
# from csv import DictReader
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.safestring import mark_safe
from django.http import HttpRequest, HttpResponse
from .models import *


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'createdAt',
        # 'profile',
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
        # 'profile',
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

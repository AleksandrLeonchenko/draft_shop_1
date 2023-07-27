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


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description']
    list_display_links = ['id', 'title', 'description']
    search_fields = ['id', 'title']
    save_on_top = True

    def get_html_image(self, object):
        if object.photo:
            return mark_safe(f"<img src='{object.image.url}' width=50>")

    get_html_image.short_description = "Миниатюра"


class ProductInstanceAdminForm(forms.ModelForm):
    """
    Форма с виджетом ckeditor
    """
    full_description = forms.CharField(label='Описание', widget=CKEditorUploadingWidget())


class ProductInstanceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'item_number',
        'free_delivery',
        'price',
        'count',
        'available',
        'date',
        'updated_date',
        'archived',
        'category',
        'ogr_tirag',
    )
    list_display_links = (
        'id',
        'title',
        'item_number',
        'free_delivery',
        'price',
        'count',
        'available',
        'date',
        'updated_date',
        'archived',
        'category',
        'ogr_tirag',
    )
    list_filter = ('available', 'date')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ['id', 'title']
    readonly_fields = ('date', 'updated_date', 'get_html_image')
    ordering = ['date']
    save_on_top = True

    def get_html_image(self, object):
        if object.photo:
            return mark_safe(f"<img src='{object.image.url}' width=50>")

    get_html_image.short_description = "Миниатюра"

    # def description_short(self, obj: ProductInstance):
    #     if len(obj.description) < 48:
    #         return obj.description
    #     return obj.description[:48] + "..."

    def description_short(self, object) -> str:
        if len(object.description) < 15:
            return object.description
        return object.description[:15] + "..."


class PropertyTypeProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ['id']


class PropertyInstanceProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'product', 'name')
    list_display_links = ('id', 'value', 'product', 'name')
    search_fields = ('value',)
    prepopulated_fields = {"slug": ("value",)}
    ordering = ['product']


class ImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'src', 'alt', 'product', 'category')
    list_display_links = ('id', 'title', 'src', 'alt', 'product', 'category')
    search_fields = ('title',)


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        # 'email',
        'rate',
        # 'ip',
        'text',
        'date',
        'active',
        'product',
        'parent',
    )
    list_display_links = (
        'id',
        'author',
        # 'email',
        'rate',
        # 'ip',
        'text',
        'date',
        # 'active'
    )
    list_editable = ('active',)
    search_fields = ('author', 'product')
    # prepopulated_fields = {"slug": ("product",)}


class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'fullName',
        'email',
        'phone',
    ]
    list_display_links = [
        'id',
        'user',
        'fullName',
        'email',
        'phone',
    ]
    search_fields = ['id', 'user']
    ordering = ['id']
    prepopulated_fields = {"slug": ("user",)}


class TagsAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']
    search_fields = ['id']
    ordering = ['id']


class RateAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'value',
    ]
    list_display_links = [
        'id',
        'value',
    ]
    search_fields = ['id', 'value']
    ordering = ['id']
    # prepopulated_fields = {"slug": ("value",)}


class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'rating_value',
        'product',
        'ip',
        'author',
    ]
    list_display_links = [
        'id',
        'rating_value',
        'product',
        'ip',
        'author',
    ]
    search_fields = ['id', 'rating_value']
    ordering = ['id']
    # prepopulated_fields = {"slug": ("rating_value",)}


class PurchaseListAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'payment_method',
        'delivery_method',
        'payment_status',
        'delivery_status',
        'time_create',
        'price',
    ]
    list_display_links = [
        'id',
        'user',
        'payment_method',
        'delivery_method',
        'payment_status',
        'delivery_status',
        'time_create',
        'price',
    ]
    search_fields = ['id', 'user']
    ordering = ['id']


class OrderAdmin(admin.ModelAdmin):
    # change_list_template = "shop/orders_changelist.html"
    list_display = [
        'id',
        'created',
        'updated',
        'user',
        'status',
        'payment'
    ]
    list_display_links = [
        'id',
        'created',
        'updated',
        'user',
        'status',
        'payment'
    ]
    search_fields = ['id']
    ordering = ['id']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'price',
        'quantity',
        'product'
    ]
    list_display_links = [
        'id',
        'price',
        'quantity'
    ]
    search_fields = ['id']
    ordering = ['id']


admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductInstance, ProductInstanceAdmin)
admin.site.register(PropertyTypeProduct, PropertyTypeProductAdmin)
admin.site.register(PropertyInstanceProduct, PropertyInstanceProductAdmin)
admin.site.register(Images, ImagesAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(PurchaseList, PurchaseListAdmin)
admin.site.register(Tags, TagsAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)

admin.site.site_title = 'Админ-панель сайта diploma_shop'
admin.site.site_header = 'Админ-панель сайта diploma_shop'

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
    list_display = ['id', 'title', 'description', 'parent']
    list_display_links = ['id', 'title', 'description', 'parent']
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
        'freeDelivery',
        'price',
        'count',
        'available',
        'date',
        'updated_date',
        'archived',
        'category',
        'order'
    )
    list_display_links = (
        'id',
        'title',
        'item_number',
        'freeDelivery',
        'price',
        'count',
        'available',
        'date',
        'updated_date',
        'archived',
        'category',
        'order'
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


class ProductImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'alt', 'src', 'product')
    list_display_links = ('id', 'alt', 'src', 'product')
    search_fields = ('alt',)


class CategoryImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'alt', 'src')
    list_display_links = ('id', 'alt', 'src')
    search_fields = ('alt',)



class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'rate',
        'text',
        'date',
        'active',
        'product',
        'parent',
    )
    list_display_links = (
        'id',
        'author',
        'rate',
        'text',
        'date',
    )
    list_editable = ('active',)
    search_fields = ('author', 'product')




class TagAdmin(admin.ModelAdmin):
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





admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductInstance, ProductInstanceAdmin)
admin.site.register(PropertyTypeProduct, PropertyTypeProductAdmin)
admin.site.register(PropertyInstanceProduct, PropertyInstanceProductAdmin)
admin.site.register(ProductImages, ProductImagesAdmin)
admin.site.register(CategoryImages, CategoryImagesAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Rate, RateAdmin)


admin.site.site_title = 'Админ-панель приложения app_products'
admin.site.site_header = 'Админ-панель приложения app_products'

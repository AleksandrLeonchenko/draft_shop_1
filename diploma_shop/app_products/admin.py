from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *
from typing import List, Tuple, Dict, Type, Union, Optional


class CategoryAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'title', 'description', 'parent']
    list_display_links: List[str] = ['id', 'title', 'description', 'parent']
    search_fields: List[str] = ['id', 'title']
    save_on_top: bool = True

    def get_html_image(self, object) -> Optional[str]:
        if object.photo:
            return mark_safe(f"<img src='{object.image.url}' width=50>")

    get_html_image.short_description = "Миниатюра"


class ProductInstanceAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = (
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
    list_display_links: Tuple[str, ...] = (
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
    list_filter: Tuple[str, str] = ('available', 'date')
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("title",)}
    search_fields: List[str] = ['id', 'title']
    readonly_fields: Tuple[str, ...] = ('date', 'updated_date', 'get_html_image')
    ordering: List[str] = ['date']
    save_on_top: bool = True

    def get_html_image(self, object) -> Optional[str]:
        if object.photo:
            return mark_safe(f"<img src='{object.image.url}' width=50>")

    get_html_image.short_description = "Миниатюра"

    def description_short(self, object) -> str:
        if len(object.description) < 15:
            return object.description
        return object.description[:15] + "..."


class PropertyTypeProductAdmin(admin.ModelAdmin):
    list_display: Tuple[str, str] = ('id', 'name')
    list_display_links: Tuple[str, str] = ('id', 'name')
    search_fields: Tuple[str] = ('name',)
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("name",)}
    ordering: List[str] = ['id']


class PropertyInstanceProductAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ('id', 'value', 'product', 'name')
    list_display_links: Tuple[str, ...] = ('id', 'value', 'product', 'name')
    search_fields: Tuple[str] = ('value',)
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("value",)}
    ordering: List[str] = ['product']


class ProductImagesAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ('id', 'alt', 'src', 'product')
    list_display_links: Tuple[str, ...] = ('id', 'alt', 'src', 'product')
    search_fields: Tuple[str] = ('alt',)


class CategoryImagesAdmin(admin.ModelAdmin):
    list_display: Tuple[str, str, str] = ('id', 'alt', 'src')
    list_display_links: Tuple[str, str, str] = ('id', 'alt', 'src')
    search_fields: Tuple[str] = ('alt',)


class ReviewAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = (
        'id',
        'author',
        'rate',
        'text',
        'date',
        'active',
        'product',
        'parent',
    )
    list_display_links: Tuple[str, ...] = (
        'id',
        'author',
        'rate',
        'text',
        'date',
    )
    list_editable: Tuple[str] = ('active',)
    search_fields: Tuple[str, str] = ('author', 'product')


class TagAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'name']
    list_display_links: List[str] = ['id', 'name']
    search_fields: List[str] = ['id']
    ordering: List[str] = ['id']


class RateAdmin(admin.ModelAdmin):
    list_display: List[str] = [
        'id',
        'value',
    ]
    list_display_links: List[str] = [
        'id',
        'value',
    ]
    search_fields: List[str] = ['id', 'value']
    ordering: List[str] = ['id']


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

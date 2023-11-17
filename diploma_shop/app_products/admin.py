from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *
from typing import List, Tuple, Dict, Type, Union, Optional


class CategoryAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'title', 'description', 'parent']
    list_display_links: List[str] = ['id', 'title', 'description', 'parent']
    search_fields: List[str] = ['id', 'title']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели

    def get_html_image(self, object) -> Optional[str]:  # Метод для отображения HTML изображения в админ- панели
        if object.photo:
            return mark_safe(f"<img src='{object.image.url}' width=50>")

    get_html_image.short_description = "Миниатюра"


class ProductInstanceAdmin(admin.ModelAdmin):
    list_display: List[str] = [
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
    ]
    list_display_links: List[str] = [
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
    ]
    list_filter: List[str] = ['available', 'date']
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("title",)}  # автозаполнение поля
    search_fields: List[str] = ['id', 'title']
    readonly_fields: List[str] = ['date', 'updated_date', 'get_html_image']  # только для чтения
    ordering: List[str] = ['date']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели

    def get_html_image(self, object) -> Optional[str]:  # Метод для отображения HTML изображения в админ- панели
        if object.photo:
            return mark_safe(f"<img src='{object.image.url}' width=50>")

    get_html_image.short_description = "Миниатюра"

    def description_short(self, object) -> str:  # Метод для вывода краткого описания в админ- панели
        if len(object.description) < 15:
            return object.description
        return object.description[:15] + "..."


class PropertyTypeProductAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'name']
    list_display_links: List[str] = ['id', 'name']
    search_fields: List[str] = ['name']
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("name",)}  # автозаполнение поля
    ordering: List[str] = ['id']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


class PropertyInstanceProductAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'value', 'product', 'name']
    list_display_links: List[str] = ['id', 'value', 'product', 'name']
    search_fields: List[str] = ['value']
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("value",)}  # автозаполнение поля
    ordering: List[str] = ['product']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


class ProductImagesAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'alt', 'src', 'product']
    list_display_links: List[str] = ['id', 'alt', 'src', 'product']
    search_fields: List[str] = ['alt']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


class CategoryImagesAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'alt', 'src']
    list_display_links: List[str] = ['id', 'alt', 'src']
    search_fields: List[str] = ['alt']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


class ReviewAdmin(admin.ModelAdmin):
    list_display: List[str] = [
        'id',
        'author',
        'rate',
        'text',
        'date',
        'active',
        'product',
        'parent',
    ]
    list_display_links: List[str] = [
        'id',
        'author',
        'rate',
        'text',
        'date',
    ]
    list_editable: List[str] = ['active']
    search_fields: List[str] = ['author', 'product']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


class TagAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'name']
    list_display_links: List[str] = ['id', 'name']
    search_fields: List[str] = ['id']
    ordering: List[str] = ['id']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


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
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


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

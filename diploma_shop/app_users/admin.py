from django.contrib import admin
from typing import List, Tuple, Dict, Type

from .models import AvatarsImages, Profile


class AvatarsImagesAdmin(admin.ModelAdmin):
    list_display: List[str] = ['id', 'alt', 'src']
    list_display_links: List[str] = ['id', 'alt', 'src']
    search_fields: List[str] = ['alt']
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


class ProfileAdmin(admin.ModelAdmin):
    list_display: List[str] = [
        'id',
        'user',
        'fullName',
        'phone',
    ]
    list_display_links: List[str] = [
        'id',
        'user',
        'fullName',
        'phone',
    ]
    search_fields: List[str] = ['id', 'user']
    ordering: List[str] = ['id']
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("user",)}  # автозаполнение поля
    save_on_top: bool = True  # кнопка "Сохранить" в верхней части страницы редактирования объекта в админ- панели


admin.site.register(AvatarsImages, AvatarsImagesAdmin)
admin.site.register(Profile, ProfileAdmin)

admin.site.site_title = 'Админ-панель приложения app_users'
admin.site.site_header = 'Админ-панель приложения app_users'

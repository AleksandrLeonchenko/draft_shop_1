from django.contrib import admin
from .models import *
from typing import List, Tuple, Dict, Type


class AvatarsImagesAdmin(admin.ModelAdmin):
    list_display: Tuple[str, str, str] = ('id', 'alt', 'src')
    list_display_links: Tuple[str, str, str] = ('id', 'alt', 'src')
    search_fields: Tuple[str] = ('alt',)


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
    prepopulated_fields: Dict[str, Tuple[str]] = {"slug": ("user",)}


admin.site.register(AvatarsImages, AvatarsImagesAdmin)
admin.site.register(Profile, ProfileAdmin)

admin.site.site_title = 'Админ-панель приложения app_users'
admin.site.site_header = 'Админ-панель приложения app_users'

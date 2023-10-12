
from django.contrib import admin
from .models import *


class AvatarsImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'alt', 'src')
    list_display_links = ('id', 'alt', 'src')
    search_fields = ('alt',)


class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'fullName',
        'phone',
    ]
    list_display_links = [
        'id',
        'user',
        'fullName',
        'phone',
    ]
    search_fields = ['id', 'user']
    ordering = ['id']
    prepopulated_fields = {"slug": ("user",)}


admin.site.register(AvatarsImages, AvatarsImagesAdmin)
admin.site.register(Profile, ProfileAdmin)

admin.site.site_title = 'Админ-панель приложения app_users'
admin.site.site_header = 'Админ-панель приложения app_users'

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

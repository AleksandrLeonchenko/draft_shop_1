from django.shortcuts import render
from django.views.generic import TemplateView


class DraftView(TemplateView):
    template_name = "products/draft.html"

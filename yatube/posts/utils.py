from django.core.paginator import Paginator
from django.conf import settings


def page_paginator(queryset, request):
    paginator = Paginator(queryset, settings.NUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

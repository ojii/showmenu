import json
from cms.api import create_page
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def _create_pages(pages, parent):
    for data in pages:
        page = create_page(
            title=data['title'],
            template='dummy.html',
            language='en',
            parent=parent,
            published=True,
            in_navigation=True,
        )
        _create_pages(data['items'], page)


def home(request):
    return render(request, 'home.html')


@require_POST
@csrf_exempt
def show_menu(request):
    data = json.loads(request.body.decode("utf-8"))
    _create_pages(data['tree'], None)
    context = {
        'from': data['from'],
        'to': data['to'],
        'extra_inactive': data['extra_inactive'],
        'extra_active': data['extra_active'],
    }
    return render(
        request,
        'menu.json',
        context,
        content_type='application/json'
    )

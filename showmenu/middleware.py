from cms.models import Page
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import call_command


class ShowMenuMiddleware(object):
    def process_request(self, request):
        call_command('syncdb', interactive=False)
        settings.SITE_ID = request.site_id = Site.objects.create().pk

    def process_response(self, request, response):
        if getattr(request, 'site_id', False):
            for page in Page.objects.filter(site_id=request.site_id):
                page.placeholders.all().delete()
                page.delete()
            Site.objects.get(pk=request.site_id).delete()
        return response

import json
import sys
from cms.api import create_page
from cms.models import Page
from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.template.loader import render_to_string
from django.test import RequestFactory


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


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        with open('/dev/null', 'w') as devnull:
            call_command(
                'syncdb',
                interactive=False,
                stdout=devnull,
                stderr=devnull,
                verbosity=0,
            )
        self.from_level = 0
        self.to_level = 100
        self.extra_inactive = 100
        self.extra_active = 100
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.stdout = self.stdout._out
        self.run = True

        while self.run:
            header = sys.stdin.readline()
            command, payload_length = header.split(':')
            payload_length = int(payload_length)
            payload = sys.stdin.read(payload_length)
            arguments = json.loads(payload)
            handler = getattr(self, 'handle_{}'.format(command))
            handler(*arguments)
            self.stdout.flush()

    def write_line(self, line):
        self.write('{}\n'.format(line))

    def write(self, data):
        self.stdout.write(data)

    def write_package(self, data):
        self.write_line(len(data))
        self.write(data)

    def handle_set_tree(self, tree):
        Page.objects.all().delete()
        _create_pages(tree, None)
        self.render_menu()

    def handle_stop(self):
        self.run = False

    def handle_set_argument(self, arg, value):
        setattr(self, arg, int(value))
        self.render_menu()

    def render_menu(self):
        context = {
            'from': self.from_level,
            'to': self.to_level,
            'extra_inactive': self.extra_inactive,
            'extra_active': self.extra_active,
            'request': self.request,
        }
        self.write_package(render_to_string(
            'menu.json',
            context,
        ))

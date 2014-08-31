import json
import sys
from cms.api import create_page
from cms.models import Page, Title
import dictdiffer
from django.conf import settings
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
            language=settings.LANGUAGE_CODE,
            parent=parent,
            published=True,
            in_navigation=True,
        )
        _create_pages(data['items'], page)


def get_page_by_node(node):
    return Title.objects.public().get(title=node['title']).page


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
        self.tree = None

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
        def _key_index_to_page(baseqs, key, *extra):
            indices = list(
                map(int, filter(bool, key.split('.')[::2]))
            ) + list(extra)
            queryset = baseqs.filter(level=0)
            page = None
            while indices:
                page = queryset[indices.pop(0)]
                if indices:
                    queryset = page.get_children()
            if page is None:
                page = queryset[0]
            return page

        def _add(key, index, data):
            page = _key_index_to_page(Page.objects.public(), key)
            if index == 0:
                create_page(
                    title=data['title'],
                    template='dummy.html',
                    language=settings.LANGUAGE_CODE,
                    parent=page,
                    position='first-child',
                    published=True,
                    in_navigation=True,
                )
            else:
                left = page.get_children()[index - 1]
                child = create_page(
                    title=data['title'],
                    template='dummy.html',
                    language=settings.LANGUAGE_CODE,
                    parent=page,
                    in_navigation=True,
                )
                child.move_to(left, 'right')
                child.publish(settings.LANGUAGE_CODE)

        def add(key, items):
            for index, data in items:
                _add(key, index, data)

        def _remove(key, index):
            page = _key_index_to_page(Page.objects.public(), key, index)
            page.delete()

        def remove(key, items):
            for index, _ in items:
                _remove(key, index)

        def change(key, value):
            field = key.split('.')[-1]
            if field != 'title':
                return
            page = _key_index_to_page(Page.objects.drafts(), key)
            page.title_set.filter(
                language=settings.LANGUAGE_CODE
            ).update(
                title=value[1]
            )
            page.publish(settings.LANGUAGE_CODE)

        actions = {
            'add': add,
            'remove': remove,
            'change': change,
        }
        if self.tree is None:
            sys.stderr.write('No tree to diff against\n')
            Page.objects.all().delete()
            _create_pages(tree, None)
        else:
            diff = dictdiffer.diff(self.tree, tree)
            sys.stderr.write('Diff: {}\n'.format(
                list(dictdiffer.diff(self.tree, tree))
            ))
            '''
            [
                ('change', '2.title', ('3. unicorn-zapper', '4. romantic-transclusion')),
                ('change', '2.id', (3, 4)),
                ('change', '2.$$hashKey', ('009', '00A')),
                ('change', '3.title', ('4. romantic-transclusion', '3. unicorn-zapper')),
                ('change', '3.id', (4, 3)),
                ('change', '3.$$hashKey', ('00A', '009'))]
            '''
            for action, keystring, value in diff:
                actions[action](keystring, value)
        self.tree = tree
        sys.stderr.flush()
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

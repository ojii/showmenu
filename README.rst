########
showmenu
########

An app to preview how the ``show_menu`` template tag in django CMS would render
a given page tree. **Not for the faint of heart**!

Installing
**********

Clone project, make virtualenv, install ``requirements.txt``,
run ``foreman start``.

How it works
************

``app.py`` is the public facing HTTP/WS interface. On startup, it loads all
static files into memory as well as the index page. It then serves these over
HTTP to users.

When a user visits the site (at ``/``), they connect to the app via a
websocket.

Once a websocket connection is established, the app starts a long running
Django management command for that websocket with which it communicates over
stdin/stdout.

When the app sends a command to the management command, it sends the command
name, followed by a colon, followed by the length of the payload, followed
by a newline character, followed by the payload (encoded as UTF-8). For example
to select ``to_level`` to ``2``, it would send: ``set_attribute:1\n2``.

The management command responds with the length of the payload, followed by a
newline, followed by the actual data (encoded as UTF-8). A simple tree with a
single page with title ``Home`` would look something like this:
``40\n[{"title": "Home", "url": "/", "id": 2}]``

The management command supports two *commands*: ``set_tree`` and
``set_attribute``.

``set_tree`` is followed by a page tree in an ``angular-ui-tree`` compatible
format. On the first call, it simply creates the tree in the in-memory Sqlite
database. On subsequent calls, it diffs the trees with the last tree it got
and modifies the database accordingly. It then returns the menu tree. Both the
input and the output trees are UTF-8 encoded JSON objects.

``set_attribute`` sets one of the four arguments to ``show_menu`` (
``from_level``, ``to_level``, ``extra_inactive``, ``extra_active``) and returns
the menu tree.

To generate the menu tree to return, the management command uses a custom
Django template that calls ``show_menu`` with a custom template, which directly
generates JSON.

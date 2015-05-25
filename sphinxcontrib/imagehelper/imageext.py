import os
import cgi
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image, Figure
from sphinxcontrib.imagehelper.utils import get_imagedir, is_outdated


class image_node(nodes.General, nodes.Element):
    pass


def on_builder_inited(app):
    Image.option_spec['option'] = directives.unchanged
    Figure.option_spec['option'] = directives.unchanged


def on_doctree_read(app, doctree):
    for image in doctree.traverse(nodes.image):
        options = cgi.parse_qs(image.get('option', ''))
        for name in options:
            for value in options.get(name):
                image[name] = value


def on_doctree_resolved(app, doctree, docname):
    for image in doctree.traverse(nodes.image):
        ext = os.path.splitext(image['uri'].lower())[1][1:]
        if ext in app.imageext_types:
            name, handler = app.imageext_types[ext]
            handler(app).visit(docname, image)

    for image in doctree.traverse(image_node):
        name = image['imageext_type']
        for name, handler in app.imageext_types.values():
            if name == image['imageext_type']:
                handler(app).visit(docname, image)


class ImageExtHandler(object):
    def __init__(self, app):
        self.app = app
        self.warn = app.warn

    def visit(self, docname, image_node):
        rel_imagedir, abs_imagedir = get_imagedir(self.app, docname)
        basename = self.get_filename_for(image_node)
        srcpath = os.path.join(self.app.srcdir, image_node['uri'])
        abs_imgpath = os.path.join(abs_imagedir, basename)

        if is_outdated(srcpath, abs_imgpath):
            ret = self.convert(image_node, srcpath, abs_imgpath)
        else:
            ret = True

        if ret:
            rel_imgpath = os.path.join(rel_imagedir, basename)
            newnode = nodes.image(**image_node.attributes)
            newnode['candidates'] = {'*': rel_imgpath}
            newnode['uri'] = rel_imgpath
            image_node.replace_self(newnode)

    def get_filename_for(self, node):
        return os.path.splitext(node['uri'])[0] + '.png'

    def convert(self, node, filename, to):
        pass


def add_image_type(app, name, ext, handler):
    if not hasattr(app, 'imageext_types'):
        app.add_node(image_node)
        app.connect('builder-inited', on_builder_inited)
        app.connect('doctree-read', on_doctree_read)
        app.connect('doctree-resolved', on_doctree_resolved)
        app.imageext_types = {}

    if ext.startswith('.'):
        ext = ext[1:]

    app.imageext_types[ext] = (name, handler)

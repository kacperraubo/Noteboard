from django import template

from texteditor.models import Folder, Note
from texteditor.anonymous import Folder as AnonymousFolder, Note as AnonymousNote

register = template.Library()


@register.filter
def get_type(value):
    if type(value) in [Folder, AnonymousFolder]:
        return "folder"

    elif type(value) in [Note, AnonymousNote]:
        return "note"

    return type(value)

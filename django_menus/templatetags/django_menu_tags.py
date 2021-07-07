from django import template
from django.utils.safestring import mark_safe
from django_menus.menu import MenuItem
from django_menus import DUMMY_MENU_ID, DUMMY_MENU_SLUG

register = template.Library()


@register.simple_tag(takes_context=True)
def template_content(context, content_name):
    return mark_safe(f'<div id={content_name}>{context[content_name]}</div>')


@register.simple_tag(takes_context=True)
def menu_content(context, content_name):
    return mark_safe(f'<div id={content_name}>{context["menus"][content_name].render()}</div>')


@register.simple_tag()
def display_button(**kwargs):
    return MenuItem(**kwargs).render()


@register.simple_tag
def show_menu(menu, **kwargs):
    html = menu.render()
    for key, value in kwargs.items():
        if key == 'pk':
            html = html.replace(str(DUMMY_MENU_ID), str(value))
        elif key == 'slug':
            html = html.replace(str(DUMMY_MENU_SLUG), str(value))
        else:
            html = html.replace(str(key), str(value))
    return mark_safe(html)

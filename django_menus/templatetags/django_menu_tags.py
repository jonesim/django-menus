from django import template
from django.utils.safestring import mark_safe

from django_menus.menu import HtmlMenu, MenuItem

register = template.Library()


@register.simple_tag(takes_context=True)
def template_content(context, content_name):
    return mark_safe(f'<div id={content_name}>{context[content_name]}</div>')


@register.simple_tag(takes_context=True)
def menu_content(context, content_name):
    return mark_safe(f'<div id={content_name}>{context["menus"][content_name].render()}</div>')


@register.simple_tag(takes_context=True)
def display_button(context, **kwargs):

    menu = HtmlMenu(context['request'], 'button_group').add_items(
        MenuItem(**kwargs),
    )
    return menu.render()

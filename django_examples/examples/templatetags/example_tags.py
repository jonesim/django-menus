from ajax_helpers.utils import random_string
from django import template
from django.utils.safestring import mark_safe
from examples.views import setup_main_menu

from examples.globals import DUMMY_MENU_DROP_DOWN_ID, DUMMY_MENU_ID, DUMMY_MENU_SLUG

register = template.Library()


@register.simple_tag(takes_context=True)
def main_menu(context):
    return setup_main_menu(context['request']).render()


@register.simple_tag
def show_menu(menu, **kwargs):
    new_id = random_string()
    html = menu.render().replace(str(DUMMY_MENU_DROP_DOWN_ID), str(new_id))
    for key, value in kwargs.items():
        if key == 'pk':
            html = html.replace(str(DUMMY_MENU_ID), str(value))
        elif key == 'slug':
            html = html.replace(str(DUMMY_MENU_SLUG), str(value))
        else:
            html = html.replace(str(key), str(value))

    return mark_safe(html)

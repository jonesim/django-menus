from django import template
from menu_examples.views import setup_main_menu


register = template.Library()


@register.simple_tag(takes_context=True)
def main_menu(context):
    return setup_main_menu(context['request']).render()

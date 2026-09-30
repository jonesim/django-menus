from ajax_helpers.html_include import SourceBase


class Bootstrap5(SourceBase):
    """Bootstrap 5 from the CDN, so the examples can be looked at on either version.

    ajax_helpers ships Bootstrap 4 (``ajax_helpers.includes.Bootstrap``, pinned at 4.6.0) and
    has no Bootstrap 5 equivalent upstream yet, so the example app carries its own rather than
    wait for one. This mirrors ``cards_examples.includes.Bootstrap5`` in django-cards.

    The bundle loads *after* the ``ajax_helpers`` group, and that order matters twice over:

    - jQuery comes first, so Bootstrap 5 registers its jQuery plugin interface and
      ``ajax_helpers.tooltip`` keeps working unchanged;
    - the ``ajax_helpers`` group also brings Popper 1, and Bootstrap 5's bundle keeps its own
      Popper 2 private rather than publishing ``window.Popper``. So ``django_menus.js`` still
      finds the Popper 1 it was written against on both paths.
    """
    cdn_path = 'cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/'
    js_filename = 'bootstrap.bundle.min.js'
    css_filename = 'bootstrap.min.css'


packages = {
    'bootstrap5': [Bootstrap5],
}

from django.urls import include, path

from tests import views_invalid as views

nested_patterns = ([
    path('missing-args/', views.MissingUrlArgs.as_view(), name='missing_url_args'),
], 'broken')

urlpatterns = [
    path('unknown-section/', views.UnknownSection.as_view(), name='unknown_section'),
    path('unknown-group/', views.UnknownGroup.as_view(), name='unknown_group'),
    path('missing-group/', views.MissingGroup.as_view(), name='missing_group'),
    path('ambiguous/', views.Ambiguous.as_view(), name='ambiguous_a'),
    path('ambiguous/', views.Ambiguous.as_view(), name='ambiguous_b'),
    path('unknown-url-name/', views.UnknownUrlName.as_view(), name='unknown_url_name'),
    path('not-an-entry/', views.NotAnEntry.as_view(), name='not_an_entry'),
    path('no-display/', views.NoDisplay.as_view(), name='no_display'),
    path('button-clash/', views.ButtonDefaultClash.as_view(), name='button_clash'),

    # the include itself captures an argument the entry does not supply
    path('section/<int:pk>/', include(nested_patterns)),
]

from django.urls import path
from django.views.generic.base import RedirectView
import menu_examples.views as views


urlpatterns = [
    path('menu', views.View1.as_view(), name='main'),
    path('', RedirectView.as_view(pattern_name='main', )),
    path('menu-redirect/', RedirectView.as_view(pattern_name='main', ), name='django-tab-menus'),
    path('intpath/<int:int>', views.View2.as_view(), name='int_path'),

    path('ajax-tab-example/', views.AjaxTabExample.as_view(), name='ajaxtab'),
    path('ajax-tab-example/tab2/', views.AjaxTabExample2.as_view(), name='content2'),

    path('view1/', views.View1.as_view(), name='string'),
    path('view1/', views.View1.as_view(), name='url_name'),
    path('view1/', views.View1.as_view(), name='view1'),
    path('view2/', views.View2.as_view(), name='view2'),
    path('view3/', views.View3.as_view(), name='view3'),
    path('view4/', views.View4.as_view(), name='view4'),

    path('modals/', views.ModalExamples.as_view(), name='modal_examples'),
    path('modal/', views.TestModal.as_view(), name='test_modal'),
    path('modal/<str:slug>', views.TestModal.as_view(), name='test_modal'),
    path('modal64/<str:base64>', views.TestModal.as_view(), name='test_modal64'),

    path('source_code/<str:slug>', views.SourceCodeModal.as_view(), name='source_code')
]

from django.urls import path
import menu_examples.views as views


urlpatterns = [
    path('', views.View1.as_view(), name='main'),
    path('intpath/<int:int>', views.View2.as_view(), name='int_path'),

    path('ajax-tab-example/', views.AjaxTabExample.as_view(), name='ajaxtab'),
    path('ajax-tab-example/tab2/', views.AjaxTabExample2.as_view(), name='content2'),

    path('view1/', views.View1.as_view(), name='string'),
    path('view1/', views.View1.as_view(), name='url_name'),
    path('view1/', views.View1.as_view(), name='view1'),
    path('view2/', views.View2.as_view(), name='view2'),
    path('view3/', views.View3.as_view(), name='view3'),
    path('view4/', views.View4.as_view(), name='view4'),

    path('source_code/<str:slug>', views.SourceCodeModal.as_view(), name='source_code')
]

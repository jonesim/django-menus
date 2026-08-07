"""A second URLConf, used to prove the registry cache is keyed on ROOT_URLCONF."""
from django.urls import path

from tests import views

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
]

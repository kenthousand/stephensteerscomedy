from django.urls import path

from . import views

app_name = 'comedy'

urlpatterns = [
    path('', views.index, name='index'),
]

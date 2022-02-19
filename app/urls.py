
from django.urls import include, path
from . import views  
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('hello', views.say_hello, name='hello'),
    path('display_document', views.display_document)
]
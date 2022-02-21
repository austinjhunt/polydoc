
from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static
from . import views  
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    
    path('login', views.LoginView.as_view(), name='login'),
    path('register', views.RegisterView.as_view(), name='register'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('profile', views.ProfileView.as_view(), name='profile'), 

    # Document containers
    path('documentcontainer/create', views.DocumentContainerCreateView.as_view(), name='document-container-create'),
    path('documentcontainer/update/<slug:pk>', views.DocumentContainerUpdateView.as_view(), name='document-container-update'),
    path('documentcontainer/delete/<slug:pk>', views.DocumentContainerDeleteView.as_view(), name='document-container-delete'),

    # Documents 
    path('document/create', views.DocumentCreateView.as_view(), name='document-create'),
    path('document/update/<slug:pk>', views.DocumentUpdateView.as_view(), name='document-update'),
    path('document/delete/<slug:pk>', views.DocumentDeleteView.as_view(), name='document-delete'),
    path('display_document', views.display_document),

    # utility
    # POST endpoint requires trailing slash for ajax call 
    path('toggle-theme/', views.ToggleThemeView.as_view(), name='toggle-theme')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
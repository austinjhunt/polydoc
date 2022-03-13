
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
    path('documentcontainer/create', views.DocumentContainerCreateView.as_view(), name='create-document-container'),
    path('documentcontainer/import', views.DocumentContainerImportView.as_view(), name='import-google-drive-folder'),
    path('documentcontainer/update/<slug:pk>', views.DocumentContainerUpdateView.as_view(), name='update-document-container'),
    path('documentcontainer/delete/<slug:pk>', views.DocumentContainerDeleteView.as_view(), name='delete-document-container'),

    # Documents 
    path('document/create', views.DocumentCreateView.as_view(), name='create-document'),
    path('document/update/<slug:pk>', views.DocumentUpdateView.as_view(), name='update-document'),
    path('document/delete/<slug:pk>', views.DocumentDeleteView.as_view(), name='delete-document'),
    path('document/<slug:pk>/pages', views.DocumentPagesView.as_view(), name='document-pages'),
    #path('display_document', views.display_document),

    # Multiview functionality 
    path('multiview/<slug:container_id>', views.MultiView.as_view(), name='multiview'),
    # utility

    # POST endpoint requires trailing slash for ajax call 
    path('toggle-theme/', views.ToggleThemeView.as_view(), name='toggle-theme'),
    path('page-notes/<slug:pk>/', views.PageNotesEditView.as_view(), name='edit-page-notes')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# def fake(request):
#     return "fake"
# urlpatterns = [
#     path('', fake, name='fake')
# ]
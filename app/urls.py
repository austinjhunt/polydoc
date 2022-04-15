
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
    path('drive', views.DriveView.as_view(), name='drive'),
    path('drive/authenticate', views.DriveCallbackView.as_view(), name='auth'),

    # Document containers
    path('documentcontainer/create', views.DocumentContainerCreateView.as_view(), name='create-document-container'),
    path('documentcontainer/import-from-drive/', views.ImportFromDriveView.as_view(), name='import-from-drive'),
    path('documentcontainer/update/<slug:pk>', views.DocumentContainerUpdateView.as_view(), name='update-document-container'),
    path('documentcontainer/delete/<slug:pk>', views.DocumentContainerDeleteView.as_view(), name='delete-document-container'),
    path('documentcontainer/clear', views.DocumentContainerClearView.as_view(), name='document-container-clear'),

    # Documents
    path('document/create', views.DocumentCreateView.as_view(), name='create-document'),
    path('document/update/<slug:pk>', views.DocumentUpdateView.as_view(), name='update-document'),
    path('document/delete/<slug:pk>', views.DocumentDeleteView.as_view(), name='delete-document'),
    path('document/<slug:pk>/pages', views.DocumentPagesView.as_view(), name='document-pages'),
    path('document/<slug:pk>/save-notes/', views.DocumentSaveNotesView.as_view(), name='document-save-notes'),
    path('document/clear', views.DocumentClearView.as_view(), name='document-clear'),
    #path('display_document', views.display_document),

    # Multiview functionality
    path('multiview/<slug:container_id>', views.MultiView.as_view(), name='multiview'),

    # Celery & Progress monitoring
    path('task-status/view', views.TaskStatusView.as_view(), name='task-status-view'),
    path('task-status/<slug:task_id>', views.get_progress, name='task_status'),

    # POST endpoint requires trailing slash for ajax call
    path('toggle-theme/', views.ToggleThemeView.as_view(), name='toggle-theme'),
    path('page-notes/<slug:pk>/', views.PageNotesEditView.as_view(), name='edit-page-notes')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


## If re-creating DB, uncomment this; comment the above; leave path import uncommented
## then run
## python manage.py makemigrations && python manage.py migrate app
# def fake(request):
#     return "fake"
# urlpatterns = [
#     path('', fake, name='fake')
# ]
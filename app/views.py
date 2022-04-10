from .models import DocumentContainer, Document, Page
from .drive.utils import DriveAPI
from django.forms import ValidationError
from .forms import DocumentUploadForm, UserLoginForm, UserCreateForm, DocumentContainerForm
from django.shortcuts import redirect, render
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.views.generic import View, FormView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db.models import Count
import json
import os
class HomeView(View):
    def get(self, request):
        return render(
            request,
            template_name='index.html',
            context={}
        )


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('home')


class RegisterView(FormView):
    form_class = UserCreateForm
    template_name = 'forms/register.html'
    success_url = '/'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        else:
            return render(request=request, template_name=self.template_name, context={'form': self.form_class()})

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        username = self.request.POST.get('username', None)
        password = self.request.POST.get('password1', None)
        user = form.save()
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return redirect(self.success_url)


class LoginView(FormView):
    form_class = UserLoginForm
    template_name = 'forms/login.html'
    success_url = '/'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(
            request,
            template_name=self.template_name,
            context={'form': self.form_class()}
        )

    def post(self, request):
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(self.request, user)
            return redirect('home')
        else:
            form.add_error(field=None, error=ValidationError(
                "No account matches the information you provided"))
            return render(
                request=self.request,
                template_name=self.template_name,
                context={'form': form}
            )


class ProfileView(LoginRequiredMixin, FormView):
    form_class = DocumentUploadForm

    def get(self, request):
        user_document_containers = DocumentContainer.objects.filter(
            user=request.user)
        for doc_container in user_document_containers:
            setattr(
                doc_container,
                'doc_count',
                Document.objects.filter(
                    containers__in=[doc_container.id]).count()
            )
        return render(
            request=request,
            template_name='profile.html',
            context={
                'form': self.form_class(),
                'user_document_containers': user_document_containers,
                'user_documents': Document.objects.filter(user=request.user).annotate(num_pages=Count('page'))}
        )

    def form_valid(self, form):
        # Called after POSTED data has been validated
        files = form.files  # MultiValueDict with key "files"
        files = files.getlist('file')
        print(files)
        return render(
            request=self.request,
            template_name='profile.html',
            context={'form': form}
        )


class DriveView(LoginRequiredMixin, View):
    def get(self, request):
        print('drive view')
        driveAPI = DriveAPI(request=request)
        print(f'drive API created')
        if not driveAPI.has_valid_creds():
            print(f'drive API does not have valid creds; calling authorize()')
            driveAPI.authorize()
            request.session['creds'] = driveAPI.creds
            url = driveAPI.get_authorization_url()[0]
            return HttpResponseRedirect(url)
        else:
             return redirect('profile')

class DriveCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        driveAPI = DriveAPI(request=request)
        print('callback uri view')
        print(f'code = {request.GET["code"]}')
        print('calling authorize(code=...)')
        driveAPI.authorize(code=request.GET['code'])
        return redirect('profile')


class DocumentContainerCreateView(LoginRequiredMixin, CreateView):
    model = DocumentContainer
    form_class = DocumentContainerForm
    success_url = 'profile'
    login_url = 'login'
    template_name = 'forms/create-document-container.html'

    def form_valid(self, form):
        # Create document container associated with this user
        DocumentContainer(
            name=form.cleaned_data['name'],
            user=self.request.user
        ).save()
        return redirect('profile')


class ImportFromDriveView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'forms/import-google-drive-folder.html'

    def get(self, request):
        # Get folders (only folders) from Google Drive account
        drive = DriveAPI(request=request)
        if not drive.has_valid_creds():
            print('drive connection creds expired; refreshing')
            drive.refresh()
            request.session['creds'] = drive.creds
            url = drive.get_authorization_url()[0]
            return HttpResponseRedirect(url)
        if not drive.service_connected():
            drive.connect_drive_service()
        google_drive_folders = drive.get_folder_list()
        return render(
            request=request,
            template_name=self.template_name,
            context={
                'google_drive_folders': google_drive_folders
            }
        )

    def post(self, request):
        try:
            print(request.body.decode())
            print(request.__dict__)
            data = json.loads(request.body.decode())
        except Exception as e:
            print(e)
            return redirect('profile')
        selected_drive_folder_id = data['folderId']
        selected_drive_folder_name = data['folderName']
        if not selected_drive_folder_name or not selected_drive_folder_id:
            return JsonResponse({'result': 'drive folder id or name not provided'})
        drive = DriveAPI(request=request)
        if not drive.has_valid_creds():
            return JsonResponse({'result': 'drive not connected'})
        if not drive.service_connected():
            drive.connect_drive_service()

        try:
            files_in_selected_folder = drive.get_files_in_folder(folder_id=selected_drive_folder_id)
            relative_folder_path = f'/media/documents/{self.request.user.username}'
            full_folder_path = f'{settings.MEDIA_ROOT}/documents/{self.request.user.username}'
            # create a document container with same name as folder
            document_container = DocumentContainer(
                name=selected_drive_folder_name,
                user=request.user
            )
            document_container.save()
            for f in files_in_selected_folder:
                print(f'filename={f.get("name")}')
                _fname = f.get('name') + ".pdf"
                # Store pdf in database
                if len(_fname) > 15:
                    # Shorten filename if longer than 15 chars. Otherwise it causes problems.
                    _extension = _fname.split('.')[-1]
                    # If _fname is less than 20 chars, the extension doesn't get fully removed, so there are still two "."
                    # Setting end_index to resolve this
                    end_index = min(15, len(_fname)-(len(_extension) + 1))
                    _fname = f'{_fname[:end_index]}.{_extension}'
                clean_filename = _fname.replace(' ', '-').strip().lower()

                # Download file as a pdf from drive
                download_success = drive.download_file_as_pdf(
                    file_id=f.get('id'),
                    parent_folder_path=full_folder_path,
                    file_name=_fname)
                full_filename = f'{full_folder_path}/{_fname}'
                if download_success:
                    new_doc = Document(
                        notes='',
                        title=clean_filename,
                        location=f'{relative_folder_path}/{clean_filename}',
                        user=self.request.user,
                    )
                    # associate saved file with saved object
                    with open(full_filename, 'rb') as file:
                        # The default behaviour of Django's Storage class
                        # is to append a series of random characters to
                        # the end of the filename when the filename already exists which means
                        # we'll need to rename the actual file to match the saved .file property after
                        # calling .file.save()
                        new_doc.file.save(clean_filename, file)

                    os.rename(full_filename, new_doc.file.path)
                    # Update the clean_filename value to reflect the rename
                    clean_filename = new_doc.get_filename()

                    new_doc.save()
                    new_doc.containers.add(document_container.id)
                    new_doc.save()
                    new_doc.create_page_images(
                        document_relative_path=f'{full_folder_path}/{clean_filename}'
                    )
            result = 'success'
        except Exception as e:
            print(e)
            result = f'failed: {e}'
        return JsonResponse({'result': result})



class DocumentContainerClearView(LoginRequiredMixin, View):
    def get(self, request):
        DocumentContainer.objects.filter(user=request.user).delete()
        return redirect('profile')


class DocumentContainerUpdateView(LoginRequiredMixin, UpdateView):
    model = DocumentContainer
    form_class = DocumentContainerForm
    success_url = 'profile'
    login_url = 'login'
    template_name = 'forms/update-document-container.html'

    def form_valid(self, form):
        # get object id
        object_id = self.request.POST.get('objectid', None)
        if object_id:
            print(f'Object ID is {object_id}')
            doc = DocumentContainer.objects.get(id=object_id)
            doc.name = form.cleaned_data['name']
            doc.save()
        return redirect('profile')


class DocumentContainerDeleteView(LoginRequiredMixin, DeleteView):
    model = DocumentContainer
    success_url = 'profile'
    login_url = 'login'
    template_name = 'forms/delete-document-container.html'

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(DocumentContainerDeleteView, self).get_object()
        if not obj.user == self.request.user:
            raise Http404
        return obj

    def get(self, request, pk):
        try:
            doc_container = DocumentContainer.objects.get(id=pk)
            if not doc_container.user == request.user:
                raise Http404
            related_docs = Document.objects.filter(
                containers__in=[doc_container])
            related_pages = Page.objects.filter(document__in=related_docs)
            return render(
                request,
                self.template_name,
                context={
                    'related_pages': related_pages,
                    'related_docs': related_docs,
                    'object': doc_container
                }
            )
        except Exception as e:
            print(e)
            return redirect('home')

    def post(self, request, pk):
        doc_container = DocumentContainer.objects.get(id=pk)
        if not doc_container.user == request.user:
            raise Http404
        doc_container.delete()
        return redirect('profile')


class DocumentSaveNotesView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, pk):
        doc = Document.objects.get(id=pk)
        if request.user == doc.user:
            data = json.loads(request.body.decode())
            pages = data['pages']
            num_pages_saved = 0
            num_pages_failed = 0
            for p in pages:
                try:
                    page_object = Page.objects.get(id=p['id'])
                    page_object.notes = p['notes']
                    page_object.save()
                    num_pages_saved += 1
                except Exception as e:
                    print(e)
                    num_pages_failed += 1

            if num_pages_failed == 0:
                msg = f'Successfully saved notes for {num_pages_saved} pages'
            else:
                msg = (
                    f'Successfully saved notes for {num_pages_saved} pages; '
                    f'Failed to save notes for {num_pages_failed} pages'
                )

            return JsonResponse(
                {
                    'result': msg
                }
            )
        else:
            return redirect('home')

    def get(self, request):
        return redirect('home')

class DocumentClearView(LoginRequiredMixin, View):
    def get(self, request):
        Document.objects.filter(user=request.user).delete()
        return redirect('profile')

class DocumentCreateView(LoginRequiredMixin, View):
    login_url = 'login'
    success_url = 'profile'

    def get(self, request):
        return render(
            request,
            template_name='forms/create-document.html',
            context={
                'user_document_containers': DocumentContainer.objects.filter(user=request.user)
            }
        )

    def post(self, request):
        data = dict(request.POST).items()
        print(data)
        document_containers = [
            key.split('-')[1] for key, val in data if key.startswith('document_container_id-')
        ]
        files = request.FILES  # MultiValueDict with 'file' key
        files = files.getlist('file')  # list of <InMemoryUploadedFile>
        print(files)
        if len(files) == 0:
            print('empty files')
            return redirect('profile')
        # Will be used to serve on front end.
        relative_folder_path = f'/media/documents/{request.user.username}'
        full_folder_path = f'{settings.MEDIA_ROOT}/documents/{request.user.username}'
        for f in files:
            _fname = f.__dict__['_name']
            if len(_fname) > 15:
                # Shorten filename if longer than 15 chars. Otherwise it causes problems.
                _extension = _fname.split('.')[-1]
                # If _fname is less than 20 chars, the extension doesn't get fully removed, so there are still two "."
                # Setting end_index to resolve this
                end_index = min(15, len(_fname)-(len(_extension) + 1))
                _fname = f'{_fname[:end_index]}.{_extension}'
            clean_filename = _fname.replace(' ', '-').strip().lower()
            new_doc = Document(
                notes='',
                title=clean_filename,
                location=f'{relative_folder_path}/{clean_filename}',
                user=request.user,
            )
            new_doc.file.save(clean_filename, f.file)
            new_doc.save()
            for container_id in document_containers:
                new_doc.containers.add(
                    DocumentContainer.objects.get(id=container_id))
            new_doc.save()
            new_doc.create_page_images(
                document_relative_path=f'{full_folder_path}/{clean_filename}'
            )
        return redirect('profile')


class MultiView(LoginRequiredMixin, View):
    def get(self, request, container_id):
        """ Multiview - simultaneous view of all docs in a
        document container whose id is given by pk path param """
        container = DocumentContainer.objects.get(id=container_id)
        docs = Document.objects.filter(containers__in=[container])
        for d in docs:
            setattr(
                d,
                'pages',
                Page.objects.filter(document=d)
            )
        return render(
            request=request,
            template_name='multiview2.html',
            context={
                'document_container': container,
                'documents': docs,
            }
        )


class DocumentUpdateView(LoginRequiredMixin, CreateView):
    def get(self, request):
        pass


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    success_url = 'profile'
    login_url = 'login'
    template_name = 'forms/delete-document.html'

    def get(self, request, pk):
        try:
            doc = Document.objects.get(id=pk)
            if not doc.user == request.user:
                raise Http404
            related_pages = Page.objects.filter(document__in=[doc])
            return render(
                request,
                self.template_name,
                context={
                    'related_pages': related_pages,
                    'object': doc
                }
            )
        except Exception as e:
            print(e)
            return redirect('home')

    def post(self, request, pk):
        doc = Document.objects.get(id=pk)
        if not doc.user == request.user:
            raise Http404
        doc.delete()  # will auto delete related pages
        return redirect('profile')


class DocumentPagesView(LoginRequiredMixin, DetailView):
    model = Page
    template_name = 'document_viewer.html'

    def get(self, request, pk):
        document = Document.objects.filter(id=pk).first()
        print(f"Document: {document.title}")
        pages = Page.objects.filter(document=document)
        print(f"Pages: len: {len(pages)}")
        return render(
            request,
            template_name=self.template_name,
            context={
                'document': document,
                'document_pages': pages
            }
        )


class PageNotesEditView(View):
    def post(self, request, pk):
        page = Page.objects.get(id=pk)
        notes = json.loads(request.body.decode())['notes']
        page.notes = notes
        page.save()
        return JsonResponse(
            {'result': f'successfully updated notes for Page(id={pk})'}
        )


'''
def display_document(request):
    # Use credentials for whatever
    obj = DriveAPI()

    print("Attempting file download")

    # TODO: parameterize these so they aren't hardcoded

    # Change this if you want to change the id of the document that's being downloaded
    f_id = "1jN3sdlIlTy2W1Ce9OAxpie0vDJZUfOGK1MUKtlIlvuk"

    # This is the file that will be used to store the pdf version of the document on google drive
    f_name = "test_download.pdf"

    obj.FileDownload(f_id, f_name)
    try:
        return FileResponse(open(f_name, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404()
'''


class ToggleThemeView(View):
    def post(self, request):
        request.session['theme'] = json.loads(
            request.body.decode())['current_theme']
        return JsonResponse({'result': f'session updated to use theme {request.session["theme"]}'})

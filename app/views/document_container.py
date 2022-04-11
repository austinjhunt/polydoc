from ..utils import FileUtility, DriveAPI
from ..models import DocumentContainer, Document, Page
from ..forms import DocumentContainerForm
from django.shortcuts import redirect, render
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.views.generic import View,  CreateView, UpdateView, DeleteView
from storages.backends.s3boto3 import S3Boto3Storage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
import json
import os
import sys, traceback

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
            relative_folder_path = f'/media/documents/{request.user.username}'
            futil = FileUtility()
            full_folder_path = futil.generate_path_to_user_document_folder(username=request.user.username)
            # create a document container with same name as folder
            document_container = DocumentContainer(
                name=selected_drive_folder_name,
                user=request.user
            )
            document_container.save()
            for f in files_in_selected_folder:
                _fname = f.get('name') + ".pdf"
                clean_filename = futil.clean_filename(filename=_fname)
                clean_filepath = f'{full_folder_path}/{clean_filename}'
                # Download file as a pdf from drive
                download_success = drive.download_file_as_pdf(
                    file_id=f.get('id'),
                    parent_folder_path=full_folder_path,
                    file_name=clean_filename)

                if download_success:
                    print('download successful; creating doc')
                    new_doc = Document(
                        notes='',
                        title=clean_filename,
                        location=f'{relative_folder_path}/{clean_filename}',
                        user=self.request.user,
                    )
                    print('created doc')
                    # associate saved file with saved object
                    print(f'opening clean_filepath={clean_filepath}')
                    with default_storage.open(clean_filepath, 'rb') as file:
                        # The default behaviour of Django's Storage class
                        # is to append a series of random characters to
                        # the end of the filename when the filename already exists which means
                        # we'll need to rename the actual file to match the saved .file property after
                        # calling .file.save()
                        print(f'calling new_doc.file.save({clean_filename}, file)')
                        new_doc.file.save(clean_filename, file)

                    # Update the clean_filename and clean_filepath values to reflect the rename
                    clean_filename = new_doc.get_filename()
                    clean_filepath = f'{full_folder_path}/{clean_filename}'
                    print(f'saving doc')
                    new_doc.save()
                    new_doc.containers.add(document_container.id)
                    new_doc.save()
                    print(f'creating page images(document_path={clean_filepath}')
                    new_doc.create_page_images(document_path=clean_filepath)
            result = 'success'
        except Exception as e:
            print(e)
            print("-"*60)
            traceback.print_exc(file=sys.stdout)
            print("-"*60)
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
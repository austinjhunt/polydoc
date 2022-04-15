from wsgiref.util import FileWrapper
from ..utils import DriveAPI,  add_task_to_session_active_tasks
from ..tasks import import_drive_folder
from ..models import DocumentContainer, Document, Page
from ..forms import DocumentContainerForm
from django.shortcuts import redirect, render
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.generic import View,  CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import csv
import io
import zipfile

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

class DocumentContainerExportSummary(LoginRequiredMixin, View):
    def get(self, request, pk):
        dc = DocumentContainer.objects.get(id=pk)
        if dc.user == request.user:
            response = HttpResponse(
                content_type='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename={dc.name.replace(" ","-").lower()}.csv'}
            )
            writer = csv.writer(response)
            writer.writerow(['Document', 'Grade'])
            for doc in Document.objects.filter(containers__in=[dc.id]):
                print(doc)
                writer.writerow([doc.title, doc.grade])
            return response
        else:
            return redirect('profile')

class DocumentContainerExportDetail(LoginRequiredMixin, View):
    def build_doc_csv(self, doc):
        header_data = {
            'page': 'Page',
            'notes': 'Notes',
            'grade': f'Grade={doc.grade}'
        }
        mem_file = io.StringIO()
        writer = csv.DictWriter(
            mem_file, fieldnames=header_data.keys()
        )
        writer.writerow(header_data)
        for page in Page.objects.filter(document__in=[doc.id]).order_by('index'):
            writer.writerow({'page': page.index, 'notes': page.notes, 'grade': ''})
        mem_file.seek(0)
        return {'content': mem_file, 'title': doc.title}

    def get(self, request, pk):
        dc = DocumentContainer.objects.get(id=pk)
        if dc.user == request.user:
            docs = Document.objects.filter(containers__in=[dc.id])
            doc_csv_files = [self.build_doc_csv(doc=d) for d in docs]
            temp_file = io.BytesIO()
            with zipfile.ZipFile(
                temp_file, 'w', zipfile.ZIP_DEFLATED
            ) as temp_file_opened:
                for doc_csv_obj in doc_csv_files:
                    temp_file_opened.writestr(
                        f'{doc_csv_obj["title"]}.csv',
                        doc_csv_obj["content"].getvalue()
                    )
            response = HttpResponse(temp_file.getvalue())
            response['Content-Type'] = 'application/x-zip-compressed'
            response['Content-Disposition'] = f'attachment; filename={dc.name.replace(" ","-").lower()}.zip'
            return response
        else:
            return redirect('profile')

class ImportFromDriveView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'forms/import-google-drive-folder.html'
    def get(self, request):
        # Get folders (only folders) from Google Drive account
        drive = DriveAPI(request=request)
        if not drive.has_valid_creds():
            drive.refresh()
            request.session['creds'] = drive.creds
            url = drive.get_authorization_url()[0]
            return redirect(url)
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
            task_result = import_drive_folder.delay(
                userid=request.user.id,
                username=request.user.username,
                folder_id=data['folderId'],
                folder_name=data['folderName']
            )
            print(f'adding task {task_result.task_id} to session active_tasks')
            add_task_to_session_active_tasks(request=request, task_id=task_result.task_id)
            # method has been kicked off here but work is not done yet
            msg = 'import process started'
        except Exception as e:
            print(e)
            msg = f'import not started: {e}'
        return JsonResponse({'msg': msg, 'task_id': task_result.task_id})

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
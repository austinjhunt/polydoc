from ..utils import FileUtility
from ..models import Document, Page, DocumentContainer
from django.shortcuts import redirect, render
from django.http import Http404, JsonResponse
from django.views.generic import View, CreateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.conf import settings

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
        pages = Page.objects.filter(document=document)
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
        try:
            Document.objects.filter(user=request.user).delete()
        except Exception as e:
            print(e)
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
        document_containers = [
            key.split('-')[1] for key, val in data if key.startswith('document_container_id-')
        ]
        files = request.FILES  # MultiValueDict with 'file' key
        files = files.getlist('file')  # list of <InMemoryUploadedFile>
        if len(files) == 0:
            return redirect('profile')
        # Will be used to serve on front end.
        relative_folder_path = f'/media/documents/{request.user.username}'

        ## S3 storage does not work with absolute paths
        ## create a path generator function that checks if S3 is being used as storage backend.
        futil = FileUtility()
        user_documents_folder_path = futil.generate_path_to_user_document_folder(request.user.username)
        for f in files:
            _fname = f.__dict__['_name']
            clean_filename = futil.clean_filename(filename=_fname)
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
                document_path=f'{user_documents_folder_path}/{clean_filename}'
            )
        return redirect('profile')





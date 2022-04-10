from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Document, DocumentContainer, Page
class HomeView(View):
    def get(self, request):
        return render(
            request,
            template_name='index.html',
            context={}
        )

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
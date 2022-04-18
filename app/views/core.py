from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Document, DocumentContainer, Page
from ..utils import update_private_s3_image_urls_all_pages_for_doc
from django.core.cache import cache
import logging 
from django.conf import settings 
logger = logging.getLogger('PolyDoc')

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
            pages = Page.objects.filter(document=d)
            if not settings.DEBUG:
                ## S3 private URLs only apply in production
                s3_private_urls_updated_cache_key = f'doc-{d.id}-s3-image-urls-updated'
                if not cache.get(s3_private_urls_updated_cache_key):
                    logger.info(f'Key "{s3_private_urls_updated_cache_key}" not set in cache; updating S3 private URLs for page images in doc ')
                    update_private_s3_image_urls_all_pages_for_doc(pages=pages)
                    cache.set(s3_private_urls_updated_cache_key, 'updated', timeout=302400)
            setattr(
                d,
                'pages',
                pages
            )
        return render(
            request=request,
            template_name='multiview2.html',
            context={
                'document_container': container,
                'documents': docs,
            }
        )


class PrivacyPolicyView(View): 
    def get(self, request):
        return render(
            request=request,
            template_name='privacypolicy.html',
        )
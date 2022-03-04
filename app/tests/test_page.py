from distutils.command import clean
import enum
from multiprocessing import parent_process
from django.test import TestCase 
from app.models import * 
from app.utils import * 
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone 
import os
import shutil 
import pathlib 
from django.conf import settings
 


class PageTestCase(TestCase): 
    def setUp(self): 
        self.test_document_filename = 'test-document.pdf'
        self.test_document_filename_2 = 'test-document2.pdf'
        self.test_document_relative_filepath = 'app/tests/documents/test-document.pdf' 
        self.test_document_relative_filepath_2 = 'app/tests/documents/test-document2.pdf' 
        self.user = User.objects.create(
            username='testcaseuser',
            password='t3$tc4$3u$3r'
        )
        self.doc_nofile = Document.objects.create(
            notes=f'Test document notes',
            title=f'Test Document',
            location=self.test_document_relative_filepath,
            upload_datetime=timezone.now(),
            user=self.user  
        ) 
        self.doc_nofile.save()

        self.doc_withfile = Document.objects.create(
            notes=f'Test document notes',
            title=f'Test Document',
            location=self.test_document_relative_filepath_2,
            upload_datetime=timezone.now(),
            user=self.user  
        ) 
        f = open(self.test_document_relative_filepath_2, 'rb')
        self.doc_withfile.file = SimpleUploadedFile(self.test_document_filename_2 ,f.read())
        self.doc_withfile.save()    
        self.doc_withfile.create_page_images(
            document_relative_path=self.test_document_relative_filepath_2
        ) 
 
    def test_clean_filename(self):
        dirty_filename = 'THis is My document .pdf' 
        self.assertEqual(
            'this-is-my-docu.pdf',
            clean_and_shorten_filename(dirty_filename)
        )  

    def test_create_pages_from_document(self): 
        f = open(self.test_document_relative_filepath, 'rb')
        self.doc_nofile.file = SimpleUploadedFile(self.test_document_filename,f.read())
        self.doc_nofile.save()   
        self.doc_nofile.create_page_images(document_relative_path=self.test_document_relative_filepath)   
        # there are 4 pages in test-document.pdf 
        doc_pages = Page.objects.filter(document=self.doc_nofile)
        self.assertEquals(doc_pages.count(),4)
        for i,p in enumerate(doc_pages):
            self.assertTrue(os.path.exists(p.image.path)) 
            # assume true 
            self.assertEqual(f'{i}.jpg', os.path.basename(p.image.path)) 
            p.delete()

    def tearDown(self): 
        parent_folder = '/'.join(self.doc_withfile.file.path.split('/')[:-1])
        shutil.rmtree(parent_folder)  
       
    def test_autodelete_page_image_on_delete_page(self): 
        pages = Page.objects.filter(document=self.doc_withfile)
        for p in pages:
            self.assertTrue(os.path.exists(p.image.path))
            p.delete()
            self.assertFalse(os.path.exists(p.image.path))

    def test_autodelete_page_on_delete_document(self):   
        f = open(self.test_document_relative_filepath, 'rb')
        self.doc_nofile.file = SimpleUploadedFile(self.test_document_filename, f.read())
        self.doc_nofile.save()    
        self.doc_nofile.create_page_images(document_relative_path=self.test_document_relative_filepath)   
        doc_id = self.doc_nofile.id
        self.doc_nofile.delete()
        self.assertEqual(
            0,
            Page.objects.filter(document_id=doc_id).count(), 
        )

 
from ..utils import *
from django.test import TestCase
from app.models import *
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

class PageTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testcaseuser',
            password='t3$tc4$3u$3r'
        )
        self.test_document_filename = 'test-document.pdf'
        self.test_document_relative_filepath = 'app/tests/test-document.pdf'
        self.doc_nofile = Document.objects.create(
            notes=f'Test document notes',
            title=f'Test Document',
            location=self.test_document_relative_filepath,
            upload_datetime=timezone.now(),
            user=self.user
        )
        self.doc_nofile.save()


        self.test_document_filename_2 = 'test-document2.pdf'
        self.test_document_relative_filepath_2 = 'app/tests/test-document2.pdf'
        self.doc_withfile = Document.objects.create(
            notes=f'Test document notes',
            title=f'Test Document',
            location=self.test_document_relative_filepath_2,
            upload_datetime=timezone.now(),
            user=self.user
        )
        f = default_storage.open(self.test_document_relative_filepath_2, 'rb')
        self.doc_withfile.file.save(self.test_document_filename_2, f)

        self.doc_withfile.save()
        self.doc_withfile.create_page_images(
            document_path=self.test_document_relative_filepath_2
        )

    def test_clean_filename(self):
        dirty_filename = 'THis is My document .pdf'
        self.assertEqual(
            'this-is-my-docu.pdf',
            FileUtility().clean_filename(filename=dirty_filename)
        )

    def test_create_pages_from_document(self):
        f = default_storage.open(self.test_document_relative_filepath, 'rb')
        self.doc_nofile.file = SimpleUploadedFile(self.test_document_filename,f.read())
        self.doc_nofile.save()
        self.doc_nofile.create_page_images(document_path=self.test_document_relative_filepath)
        # there are 4 pages in test-document.pdf
        doc_pages = Page.objects.filter(document=self.doc_nofile)
        self.assertEquals(doc_pages.count(),4)
        for i,p in enumerate(doc_pages):
            self.assertTrue(default_storage.exists(p.get_filepath()))
            # assume true
            self.assertEqual(f'{i}.jpg', p.get_filename())
            p.delete()

    def tearDown(self):
        parent_folder = '/'.join(self.doc_withfile.get_filepath().split('/')[:-1])
        FileUtility().remove_folder_recursive(parent_folder)

    def test_autodelete_page_image_on_delete_page(self):
        pages = Page.objects.filter(document=self.doc_withfile)
        for p in pages:
            self.assertTrue(default_storage.exists(p.get_filepath()))
            p.delete()
            # page deletion does not have a post_delete signal for deleting page (image) files.
            self.assertTrue(default_storage.exists(p.get_filepath()))

        # doc deletion DOES have a post_delete signal for deleting doc file and page (image) files
        # verify that signal ; delete document; should delete all pages
        path_to_page_images_folder_for_document = get_path_to_page_images_folder(document_object=self.doc_withfile)
        self.doc_withfile.delete()
        self.assertFalse(default_storage.exists(path_to_page_images_folder_for_document))

    def test_autodelete_page_on_delete_document(self):
        f = default_storage.open(self.test_document_relative_filepath, 'rb')
        self.doc_nofile.file = SimpleUploadedFile(self.test_document_filename, f.read())
        self.doc_nofile.save()
        self.doc_nofile.create_page_images(document_path=self.test_document_relative_filepath)
        doc_id = self.doc_nofile.id
        self.doc_nofile.delete()
        self.assertEqual(
            0,
            Page.objects.filter(document_id=doc_id).count(),
        )


from multiprocessing import parent_process
from django.test import TestCase
from app.models import *
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import os
import shutil

class DocumentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testcaseuser',
            password='t3$tc4$3u$3r'
        )
        self.doc_title = 'Test Document'
        self.doc_notes = 'Test document notes'
        self.doc_location = '/some/test/location'
        self.doc_upload_datetime = timezone.now()
        self.doc_file_name = 'test_file.txt'
        self.doc_file_contents = b'test file contents!'

        self.doc = Document.objects.create(
            notes=self.doc_notes,
            title=self.doc_title,
            location=self.doc_location,
            upload_datetime=self.doc_upload_datetime,
            user=self.user
        )
        self.doc.file = SimpleUploadedFile(
            self.doc_file_name,
            self.doc_file_contents
        )
        self.doc.save()

    def tearDown(self):
        doc = Document.objects.get(id=self.doc.id)
        parent_folder = '/'.join(doc.file.path.split('/')[:-1])
        shutil.rmtree(parent_folder)

    def test_file_exists(self):
        doc = Document.objects.get(id=self.doc.id)
        self.assertTrue(
            os.path.exists(doc.file.path)
        )

    def test_autodelete_file_on_delete_document(self):
        doc = Document.objects.create(
            notes=f'Test notes on AutoDelete Test Document',
            title='AutoDelete Test Document',
            location='/some/test/location',
            upload_datetime=timezone.now(),
            user=self.user
        )
        doc.file = SimpleUploadedFile(
            "test_autodelete_file.txt",
            b'test file contents for file to be autodeleted when document is deleted!'
        )
        doc.save()
        # now delete it and verify the file is gone as well
        doc.delete()
        self.assertFalse(os.path.exists(doc.file.path))

    def test_get_document(self):
        try:
            doc = Document.objects.get(id=self.doc.id)
        except Document.DoesNotExist:
            self.assertTrue(False)
        self.assertEqual(
            self.doc_title,
            doc.title
        )
        self.assertEqual(
            self.doc_notes,
            doc.notes
        )
        self.assertEqual(
            self.doc_location,
            doc.location
        )
        self.assertEqual(
            self.doc_upload_datetime,
            doc.upload_datetime
        )

    def test_file(self):
        doc = Document.objects.get(id=self.doc.id)
        self.assertEqual(
            self.doc_file_name,
            os.path.basename(self.doc.file.name)
        )
        with open(doc.file.path, 'rb') as f:
            self.assertEqual(
                self.doc_file_contents,
                f.read()
            )


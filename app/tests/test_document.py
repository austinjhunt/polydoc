from django.test import TestCase
from app.models import *
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
class DocumentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testcaseuser',
            password='t3$tc4$3u$3r'
        )
        self.doc_title = 'Test Document'
        self.doc_notes = 'Test document notes'
        self.doc_location = 'app/tests/test-document.pdf'
        self.doc_upload_datetime = timezone.now()
        self.doc_file_name = 'test_file.txt'
        self.doc_file = default_storage.open(self.doc_location, 'rb')
        self.doc = Document.objects.create(
            notes=self.doc_notes,
            title=self.doc_title,
            location=self.doc_location,
            upload_datetime=self.doc_upload_datetime,
            user=self.user
        )
        self.doc.file = default_storage.open(self.doc_location)
        self.doc.file.save(self.doc_file_name, self.doc_file)
        self.doc.save()

    def tearDown(self):
        doc = Document.objects.get(id=self.doc.id)
        parent_folder = '/'.join(doc.get_filepath().split('/')[:-1])
        FileUtility().remove_folder_recursive(parent_folder)

    def test_file_exists(self):
        doc = Document.objects.get(id=self.doc.id)
        self.assertTrue(default_storage.exists(doc.get_filepath()))

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
        doc.delete()
        self.assertFalse(default_storage.exists(doc.get_filepath()))

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
            self.doc.get_filename()
        )
        with default_storage.open(doc.get_filepath(), 'rb') as f:
            self.assertEqual(
                self.doc_file.read(),
                f.read()
            )


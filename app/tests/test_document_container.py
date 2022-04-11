from django.test import TestCase
from app.models import *
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.utils import timezone

mytestdata = {}

class DocumentContainerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testcaseuser',
            password='t3$tc4$3u$3r'
        )
        self.test_document_path = 'app/tests/test-document.pdf'
        self.doc_container_name = 'Test Document Container'
        self.doc_container = DocumentContainer(
            user=self.user,
            name=self.doc_container_name
        )
        self.doc_container.save()
        for i in range(5):
            doc = Document(
                notes=f'Test document {i} notes',
                title=f'Test Document {i}',
                location='/some/test/location',
                upload_datetime=timezone.now(),
                user=self.user
            )
            doc.file = default_storage.open(self.test_document_path)
            doc.save()
            doc.containers.add(self.doc_container)
            doc.save()

    def tearDown(self):
        try:
            self.doc_container = DocumentContainer.objects.get(
                name=self.doc_container_name
            )
        except DocumentContainer.DoesNotExist:
            pass
        docs = Document.objects.all()
        parent_path = '/'.join(docs[0].get_filepath().split('/')[:-1])
        FileUtility().remove_folder_recursive(parent_path)

    def test_get_related_documents(self):
        related_docs =  Document.objects.filter(containers__in=[self.doc_container])
        self.assertEqual(
            5,
            related_docs.count()
        )
        for d in related_docs:
            self.assertIn(
                self.doc_container,
                d.containers.all()
            )

    def test_container_update(self):
        test_name =  'updated test name'
        self.doc_container.name = test_name
        self.doc_container.save()
        self.assertEqual(
            test_name,
            self.doc_container.name
        )
        self.doc_container.name = self.doc_container_name
        self.doc_container.save()

    def test_container_get(self):
        try:
            container = DocumentContainer.objects.get(name=self.doc_container_name)
        except DocumentContainer.DoesNotExist:
            self.assertTrue(False)

    def test_container_delete(self):
        ## Deleting a container should remove it from the many to many rel of the 5 documents
        ## and should not delete those documents
        container = DocumentContainer.objects.get(name=self.doc_container_name)
        # Force evaluate; this is a lazy query but we want it to evaluate on this line before delete
        related_docs = list(Document.objects.filter(containers__in=[self.doc_container]))
        container.delete()
        for d in related_docs:
            try:
                # ensure it still exists after container deleted
                Document.objects.get(id=d.id)
                # ensure container no longer in many to many containers property
                self.assertNotIn(
                    container,
                    d.containers.all()
                )
            except Document.DoesNotExist:
                self.assertTrue(False)




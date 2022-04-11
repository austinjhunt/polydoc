from email.policy import default
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.dispatch import receiver
import os
from pdf2image import convert_from_path, convert_from_bytes
from django.core.files.storage import default_storage
from .utils import FileUtility

# Create your models here.
def user_directory_path(instance, filename):
    print(f'saving doc file to media/documents/{instance.user}/{filename}')
    return f'media/documents/{instance.user}/{filename}'

def get_path_to_page_images_folder(document_object=None, use_site_relative_path=False):
    """ Get the path to the folder containing all of the page images for a document.
    Must use relative path if use_site_relative_path=True """
    futil = FileUtility()
    print('getting path to page images folder')
    document_location = futil.get_document_object_file_location(document_object=document_object, use_site_relative_path=use_site_relative_path)
    print(f'document_location = {document_location}')
    return f'{document_location.split(".")[0]}'

def page_image_folder_path(instance, filename):
    """
    Function to serve as argument to upload_to=<> for the image field of the Page model;
    this is where images corresponding to a given Page should be stored; one image per page;
    each image to be stored in a folder named after the corresponding Document
    """
    print(f'inside page_image_folder_path(instance, filename)')
    print(f'filename={filename}')
    return f'{get_path_to_page_images_folder(document_object=instance.document, use_site_relative_path=True)}/{filename}'

class DocumentContainer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default='Document Container')

class Document(models.Model):
    notes = models.TextField(default='')
    title = models.CharField(max_length=256, default='Document')
    location = models.CharField(max_length=512, default='')
    upload_datetime = models.DateTimeField(default=timezone.now, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path, blank=True)
    containers = models.ManyToManyField(DocumentContainer, blank=True)

    def get_filepath(self):
        """ Get path to file """
        try:
            # works on local file system storage (dev)
            path = self.file.path
        except:
            # s3 compatible
            path = self.file.url.split('amazonaws.com/')[-1].split('?AWSAccessKeyId')[0] # contains creds; remove them
        print(f'filepath = {path}')
        return path

    def get_filename(self):
        """ Get the base name of the associated file """
        filepath = self.get_filepath()
        filename = filepath.split('/')[-1]
        print(f'filepath={filepath}, so filename={filename}')
        return filename

    def create_page_images(self, document_path=""):
        """
        Create a folder named after a document (without the extension;
        document_relative_path is the relatv"""
        if self.file:
            print(f'self.file = true; document_path = {document_path}')
            # if you have saved a file
            try:
                # works for local FS storage , not for S3
                for index, image in enumerate(convert_from_path(document_path, dpi=300, fmt="jpg")):
                    new_page = Page(
                        document=self,
                        index=index,
                        notes=''
                    )
                    print('saving page')
                    new_page.save()
                    print('saving page image')
                    new_page.image.save(f'{index}.jpg', image.fp)
                    print('saved page image')
            except Exception as e:
                print(e)
                print("-"*60)
                print('Retry page image generation with S3-compatible path')
                ### FIXME
                file_byte_string = default_storage.open(document_path).read()
                for index, image in enumerate(convert_from_bytes(file_byte_string, dpi=300, fmt="jpg")):
                    new_page = Page(
                        document=self,
                        index=index,
                        notes=''
                    )
                    print('saving page')
                    new_page.save()
                    print('saving page image')
                    new_page.image.save(f'{index}.jpg', image.fp)
                    print('saved page image')


@receiver(models.signals.post_delete, sender=Document)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes document file from filesystem
    when corresponding `Document` object is deleted.
    """
    if instance.file:
        print(f'removing document files & corresponding page image folder')
        futil = FileUtility()
        path = instance.get_filepath()
        print(f'Path for doc={path}')
        futil.remove_file(path=instance.get_filepath())
        # remove the folder with the same name (i.e. pages folder for document file)
        futil.remove_folder_recursive(get_path_to_page_images_folder(document_object=instance))

class Page(models.Model):
    image = models.ImageField(upload_to=page_image_folder_path, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    notes = models.TextField(default='')

    def get_filepath(self):
        """ Get path to file """
        try:
            # works on local file system storage (dev)
            path = self.image.path
        except:
            # S3 compatible
            path = self.image.url.split('amazonaws.com/')[-1].split('?AWSAccessKeyId')[0] # contains creds; remove them
        print(f'filepath = {path}')
        return path

    def get_filename(self):
        """ Get the base name of the associated file """
        filepath = self.get_filepath()
        filename = filepath.split('/')[-1]
        print(f'filepath={filepath}, so filename={filename}')
        return filename

# Commenting this out for now; you really never do any page-level deletions.
# This receiver was breaking the document post_delete signal. Pages and page folders
# would delete but document would not.
# @receiver(models.signals.post_delete, sender=Page)
# def auto_delete_file_on_delete(sender, instance, **kwargs):
#     """
#     Deletes page/image file from filesystem
#     when corresponding `Page` object is deleted.
#     """
#     if instance.image:
#         FileUtility().remove_file(path=instance.get_filepath())

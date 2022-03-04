from django.db import models
from django.contrib.auth.models import User  
import datetime
from django.dispatch import receiver
import os  
from django.conf import settings  
from pdf2image import convert_from_path
import shutil
# Create your models here.  
def user_directory_path(instance, filename):
    return f'documents/{instance.user}/{filename}' 

def get_path_to_page_images_folder(document_object=None, relative=True):  
    """ Get the relative or absolute path to the folder containing all of the 
    page images for a document"""
    if relative:
        document_location = document_object.location.replace('/media/', '') 
    else:
        document_location = document_object.location.replace('/media/', f'{settings.MEDIA_ROOT}/')
    return f'{document_location.split(".")[0]}'

def page_image_folder_path(instance, filename): 
    # store images in sibling folder (sibling to parent document file)
    # that has same name as document minus the extension 
    return f'{get_path_to_page_images_folder(instance.document,relative=True)}/{filename}' 

class DocumentContainer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default='Document Container')

class Document(models.Model): 
    notes = models.TextField(default='')
    title = models.CharField(max_length=256, default='Document') 
    location = models.CharField(max_length=512, default='')
    upload_datetime = models.DateTimeField(default=datetime.datetime.now, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Allow multiple files to be uploaded. 
    file = models.FileField(upload_to=user_directory_path, blank=True)
    containers = models.ManyToManyField(DocumentContainer, blank=True)
    def create_page_images(self, document_relative_path=""):
        """
        Create a folder named after a document (without the extension"""
        if self.file:
            # if you have saved a file  
            for index, image in enumerate(convert_from_path(document_relative_path, dpi=300, fmt="jpg")):
                new_page = Page( 
                    document=self, 
                    index=index,
                    notes=''
                )
                new_page.save()  
                new_page.image.save(f'{index}.jpg', image.fp)  

@receiver(models.signals.post_delete, sender=Document)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes document file from filesystem
    when corresponding `Document` object is deleted.
    """
    if instance.file:
        path = instance.file.path
        if os.path.isfile(path):
            os.remove(path)
        # remove the folder with the same name 
        page_images_folder = get_path_to_page_images_folder(document_object=instance,relative=False)
        try:
            print(f'Page images folder = {page_images_folder}')
            shutil.rmtree(page_images_folder)
        except FileNotFoundError:
            pass 
        

class Page(models.Model): 
    image = models.ImageField(upload_to=page_image_folder_path, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    notes = models.TextField(default='')

@receiver(models.signals.post_delete, sender=Page)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes page/image file from filesystem
    when corresponding `Page` object is deleted.  
    """ 
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path) 

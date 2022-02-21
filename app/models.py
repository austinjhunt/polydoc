from django.db import models
from django.contrib.auth.models import User  
import datetime
from django.conf import settings 

# Create your models here.  
def user_directory_path(instance, filename):
    return f'documents/{instance.user}/{filename}' 


def page_image_folder_path(instance, filename):
    parent_doc = instance.document
    document_location = parent_doc.location.replace('/media/', '') 
    # store images in sibling folder (sibling to parent document file)
    # that has same name as document minus the extension 
    return f'{document_location.split(".")[0]}/{filename}' 

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
    
class Page(models.Model): 
    image = models.ImageField(upload_to=page_image_folder_path, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    notes = models.TextField(default='')

# Production DB URL 
#postgres://bggxldjwcelztm:b2c342e33b32e5ba8ae7d2841c27756348432569246da9395eadd2a078d77251@ec2-35-175-68-90.compute-1.amazonaws.com:5432/d5er2o0pp4glls
from statistics import mode
from django.db import models
from django.contrib.auth.models import User  
import datetime
# Create your models here.  
def user_directory_path(instance, filename):
    return f'documents/{instance.user}/{filename}' 


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
    file = models.FileField(upload_to=user_directory_path,  blank=True)
    containers = models.ManyToManyField(DocumentContainer,null=True, blank=True)
    
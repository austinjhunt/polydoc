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
    
class Page(models.Model): 
    image = models.ImageField()
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    notes = models.TextField(default='')

# Production DB URL 
#postgres://bggxldjwcelztm:b2c342e33b32e5ba8ae7d2841c27756348432569246da9395eadd2a078d77251@ec2-35-175-68-90.compute-1.amazonaws.com:5432/d5er2o0pp4glls
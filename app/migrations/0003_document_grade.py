# Generated by Django 4.0.2 on 2022-04-15 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_document_upload_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='grade',
            field=models.IntegerField(default=0),
        ),
    ]
# Generated by Django 4.0.2 on 2022-02-21 04:29

import app.models
import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(default='')),
                ('title', models.CharField(default='Document', max_length=256)),
                ('location', models.CharField(default='', max_length=512)),
                ('upload_datetime', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('file', models.FileField(blank=True, upload_to=app.models.user_directory_path)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, upload_to=app.models.page_image_folder_path)),
                ('index', models.IntegerField(default=0)),
                ('notes', models.TextField(default='')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.document')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentContainer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Document Container', max_length=256)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='document',
            name='containers',
            field=models.ManyToManyField(blank=True, to='app.DocumentContainer'),
        ),
        migrations.AddField(
            model_name='document',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

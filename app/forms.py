from pydoc import doc
from django.contrib.auth.forms import AuthenticationForm, UsernameField, UserCreationForm
from django import forms
from .validators import validate_file_extension
from .models import DocumentContainer

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs) 
    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '', 'id': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'password',
        }
    ))

class UserCreateForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '', 'id': 'hello'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={
            'class': 'form-control', 
            'id': 'password1',
        }
    ))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',  
            'id': 'password2',
        }
    ))


# Corresponds to Document model, but don't use ModelForm
class DocumentUploadForm(forms.Form):
    def user_directory_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/documents/author/<filename>
        return   f'documents/{instance.author}/{filename}'  
    document_container_choices = [
            (el.id, el.name) for el in DocumentContainer.objects.all()
        ]
    document_container_choices.insert(0, ('-','---'))
    container = forms.MultipleChoiceField(
        label='Select the containers to which these documents will belong',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
        choices=document_container_choices
    )
    file = forms.FileField( 
        validators=[validate_file_extension],
        label='Upload one or more files',
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'class':'form-control'})
    )
    
class DocumentContainerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DocumentContainerForm, self).__init__(*args, **kwargs)
        for k, v in self.fields.items():
            if self.fields[k].widget.attrs: 
                self.fields[k].widget.attrs['class'] = 'form-control'
            else: 
                self.fields[k].widget.attrs = {
                    'class': 'form-control' 
                } 
    class Meta:
        model = DocumentContainer 
        fields = ('name',)
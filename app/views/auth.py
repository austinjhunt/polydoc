from ..models import DocumentContainer, Document
from django.forms import ValidationError
from ..forms import DocumentUploadForm, UserLoginForm, UserCreateForm
from django.shortcuts import redirect, render
from django.views.generic import View, FormView
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

class LogoutView(LoginRequiredMixin, View):
    """ Logout """
    def get(self, request):
        logout(request)
        return redirect('home')

class RegisterView(FormView):
    """ Account registration """
    form_class = UserCreateForm
    template_name = 'forms/register.html'
    success_url = '/'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        else:
            return render(request=request, template_name=self.template_name, context={'form': self.form_class()})

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        username = self.request.POST.get('username', None)
        password = self.request.POST.get('password1', None)
        user = form.save()
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return redirect(self.success_url)


class LoginView(FormView):
    """ Log in / sign in view """
    form_class = UserLoginForm
    template_name = 'forms/login.html'
    success_url = '/'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(
            request,
            template_name=self.template_name,
            context={'form': self.form_class()}
        )

    def post(self, request):
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(self.request, user)
            return redirect('home')
        else:
            form.add_error(field=None, error=ValidationError(
                "No account matches the information you provided"))
            return render(
                request=self.request,
                template_name=self.template_name,
                context={'form': form}
            )


class ProfileView(LoginRequiredMixin, FormView):
    """ Profile page view """
    form_class = DocumentUploadForm
    def get(self, request):
        user_document_containers = DocumentContainer.objects.filter(
            user=request.user)
        for doc_container in user_document_containers:
            setattr(
                doc_container,
                'doc_count',
                Document.objects.filter(
                    containers__in=[doc_container.id]).count()
            )
        return render(
            request=request,
            template_name='profile.html',
            context={
                'form': self.form_class(),
                'user_document_containers': user_document_containers,
                'user_documents': Document.objects.filter(user=request.user).annotate(num_pages=Count('page'))}
        )

    def form_valid(self, form):
        # Called after POSTED data has been validated
        files = form.files  # MultiValueDict with key "files"
        files = files.getlist('file')
        print(files)
        return render(
            request=self.request,
            template_name='profile.html',
            context={'form': form}
        )
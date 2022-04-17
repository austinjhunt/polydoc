from ..utils import DriveAPI
from django.shortcuts import redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

class DriveView(LoginRequiredMixin, View):
    def get(self, request):
        driveAPI = DriveAPI(request=request)
        if not driveAPI.has_valid_creds():
            driveAPI.authorize()
            url = driveAPI.get_authorization_url()[0]
            return redirect(url)
        else:
             return redirect('dash')

class DriveCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        driveAPI = DriveAPI(request=request)
        driveAPI.authorize(code=request.GET['code'])
        return redirect('dash')
from django.views import View
from django.http import JsonResponse
import json

class ToggleThemeView(View):
    """ View for updating session theme (dark/light) """
    def post(self, request):
        request.session['theme'] = json.loads(
            request.body.decode())['current_theme']
        return JsonResponse({'result': f'session updated to use theme {request.session["theme"]}'})

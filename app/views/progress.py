import json
from django.http import JsonResponse
from celery.result import AsyncResult
from celery_progress.backend import Progress
from django.views.decorators.cache import never_cache
from django.views.generic import View
from django.shortcuts import render
from ..utils import remove_task_from_session_active_tasks

@never_cache
def get_progress(request, task_id):
    progress = Progress(AsyncResult(task_id))
    print('getting progress')
    print(progress.get_info())
    if progress.get_info()['complete']:
        print('removing task from active tasks')
        remove_task_from_session_active_tasks(request, task_id)
    return JsonResponse(progress.get_info())


class TaskStatusView(View):
    def get(self, request):
        return render(
            request=request,
            template_name='tasks.html'
        )

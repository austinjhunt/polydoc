# from django.http import JsonResponse
# from celery.result import AsyncResult
# from celery_progress.backend import Progress
# from django.views.decorators.cache import never_cache
# from django.views.generic import View
# from django.shortcuts import render
# # from ..utils import remove_task_from_user_active_tasks
# import logging 
# logger = logging.getLogger('Celery')

# @never_cache
# def get_progress(request, task_id, *args, **kwargs):
#     logger.debug(f'Getting progress of task {task_id}')
#     progress = Progress(AsyncResult(task_id))
#     if progress.get_info()['complete']:
#         print('removing task from active tasks')
#         remove_task_from_user_active_tasks(user_id=request.user.id, task_id=task_id)
#     return JsonResponse(progress.get_info())


# class TaskStatusView(View):
#     def get(self, request):
#         return render(
#             request=request,
#             template_name='tasks.html'
#         )

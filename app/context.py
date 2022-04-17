from .utils import DriveAPI
from django.conf import settings
import logging 
logger = logging.getLogger('PolyDoc')
def theme_context(request):
    # determine if first request or not
    show_loader = False
    if not 'active' in request.session:
        show_loader = True
        request.session['active'] = True

    # revert to synchronous processing for now 
    # user_active_task_keys = settings.REDIS.keys(
    #     f'active-task-{request.user.id}-*'
    # )
    # # t = [settings.REDIS.delete(k) for k in user_active_task_keys]
    # active_tasks = [settings.REDIS.get(k).decode() for k in user_active_task_keys]

    if 'theme' in request.session:
        theme = request.session['theme']
    else:
        theme = "light-theme"
    drive_authenticated = DriveAPI(request=request).has_valid_creds()
    logger.info(f'drive authenticated? -> {drive_authenticated}')
    return {
        'theme': theme,
        'show_loader': show_loader,
        'drive_authenticated': drive_authenticated ,
        #'active_tasks': active_tasks
        }

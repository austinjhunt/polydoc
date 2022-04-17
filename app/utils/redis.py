# Revert to non-async for now - this code not used with synchronous processing 
# from django.conf import settings
# import logging 

# logger = logging.getLogger(__name__)
# def add_task_to_user_active_tasks(user_id=None, task_id=None):
#     """ given user id an dtask id, store combo key in redis cache to indicate currently active """
#     logger.debug(f'Adding task {task_id} to user {user_id} active tasks')
#     key = f'active-task-{user_id}-{task_id}'
#     settings.REDIS.set(key, task_id)

# def remove_task_from_user_active_tasks(user_id=None, task_id=None):
#     """ given user id and task id, remove task from active tasks for user """    
#     logger.debug(f'Removing task {task_id} from user {user_id} active tasks')
#     key = f'active-task-{user_id}-{task_id}'
#     settings.REDIS.delete(key)
def add_task_to_session_active_tasks(request=None, task_id=None):
    """ given task id, add task id to active_tasks list stored as session variable """
    if 'active_tasks' in request.session:
        tasks = request.session['active_tasks']
        tasks.append(task_id)
    else:
        tasks = [task_id]
    request.session['active_tasks'] = tasks

def remove_task_from_session_active_tasks(request=None, task_id=None):
    """ given task id, add task id to active_tasks list stored as session variable """
    if 'active_tasks' in request.session:
        tasks = request.session['active_tasks']
        if task_id in tasks:
            tasks.remove(task_id)
        request.session['active_tasks'] = tasks
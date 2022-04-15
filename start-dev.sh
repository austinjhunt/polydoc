#!/bin/bash
sass app/static/css/app.scss > app/static/css/app.css && python manage.py collectstatic && python manage.py compress && python manage.py runserver

#### BEGIN CELERY SETTINGS ####
export BROKER_URL="redis://localhost:6379"
export CELERY_RESULT_BACKEND="redis://localhost:6379"
export CELERY_TASK_SERIALIZER="json"
export CELERY_RESULT_SERIALIZER="json"
export CELERY_TIMEZONE="US/Eastern"
#### END CELERY SETTINGS ####
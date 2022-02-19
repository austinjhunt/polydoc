#!/bin/bash
sass app/static/css/app.scss > app/static/css/app.css && python manage.py runserver
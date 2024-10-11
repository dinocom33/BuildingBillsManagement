#!/bin/bash

python manage.py runserver 0.0.0.0:8000 & celery -A BuildingBillsManagement worker --pool=solo -l info
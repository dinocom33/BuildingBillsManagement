from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

from BuildingBillsManagement import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BuildingBillsManagement.settings')

app = Celery('BuildingBillsManagement')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    worker_prefetch_multiplier=10
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

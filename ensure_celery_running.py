from celery import Celery
from subprocess import Popen
import os

# Set up the Celery app
app = Celery('BuildingBillsManagement')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

def ensure_celery_running(func):
    def wrapper(*args, **kwargs):
        inspector = app.control.inspect()
        active_workers = inspector.active()

        if not active_workers:
            print('No active Celery workers found. Starting Celery worker...')
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BuildingBillsManagement.settings')
            Popen(['celery', '-A', 'BuildingBillsManagement', 'worker', '--pool=solo', '--loglevel=info'])
        else:
            print('Celery worker is already running.')

        # Proceed to run the actual task
        return func(*args, **kwargs)

    return wrapper

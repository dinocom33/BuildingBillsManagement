from django.core.management.base import BaseCommand
from subprocess import Popen
import os

class Command(BaseCommand):
    help = 'Starts the Celery worker process'

    def handle(self, *args, **options):
        self.stdout.write('Starting Celery worker...')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BuildingBillsManagement.settings')
        Popen(['celery', '-A', 'BuildingBillsManagement', 'worker', '--pool=solo', '--loglevel=info'])

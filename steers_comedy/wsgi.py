import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'steers_comedy.settings')

application = get_wsgi_application()

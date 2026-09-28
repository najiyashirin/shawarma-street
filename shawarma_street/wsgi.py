"""WSGI entry point for Shawarma Street."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shawarma_street.settings")
application = get_wsgi_application()

"""WSGI config for jobboard_ats project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobboard_ats.settings")

application = get_wsgi_application()

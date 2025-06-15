"""
WSGI config for patrimoine_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"config.settings.{ENVIRONMENT}" if ENVIRONMENT in {"development", "testing", "staging", "production"} else "config.settings.development",
)
application = get_wsgi_application()

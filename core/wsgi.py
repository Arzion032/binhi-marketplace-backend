"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

import logging
logger = logging.getLogger(__name__)

# Add this line to see if Django is actually starting
logger.info("Django application is starting up!")
print("Django application is starting up!")  # Fallback if logging isn't working

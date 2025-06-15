from .base import *

DEBUG = False
ALLOWED_HOSTS = ["testserver"]

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Logging configuration for testing: warnings only
LOGGING["handlers"]["console"]["level"] = "WARNING"
for logger in ["django", "apps"]:
    if logger in LOGGING["loggers"]:
        LOGGING["loggers"][logger]["level"] = "WARNING"
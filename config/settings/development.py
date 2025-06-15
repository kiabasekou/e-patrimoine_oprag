#config/settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Logging configuration for development: verbose debug on console
LOGGING["handlers"]["console"]["level"] = "DEBUG"
for logger in ["django", "apps"]:
    if logger in LOGGING["loggers"]:
        LOGGING["loggers"][logger]["level"] = "DEBUG"
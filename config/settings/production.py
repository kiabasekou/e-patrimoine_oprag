from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["epatrimoine.oprag.ga"])

# Logging configuration for production: info level
LOGGING["handlers"]["console"]["level"] = "INFO"
for logger in ["django", "apps"]:
    if logger in LOGGING["loggers"]:
        LOGGING["loggers"][logger]["level"] = "INFO"
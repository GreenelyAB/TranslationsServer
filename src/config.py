import logging
from logging.config import dictConfig as _dictConfig
from os import getenv as _getenv

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from urllib.parse import urlparse as _urlparse


DEFAULT_PORT = 5512

SENTRY_DSN = _getenv("SENTRY_DSN")
ENVIRONMENT = _getenv("ENVIRONMENT")

LOGS_LOCATION = _getenv("LOGS_LOCATION")

DB_ENV = "TRANSLATIONS_SERVER_DB_URL"

TRANSLATIONS_SERVER_DB_URL = _getenv(DB_ENV)

TRANSLATIONS_SERVER_TEST_DB_URL = _getenv(
    "TRANSLATIONS_SERVER_TEST_DB_URL", "")  # optional

WORKERS = 20

DB_MIN_CONNECTIONS = 0

DB_MAX_CONNECTIONS = WORKERS

TIMEOUT_IN_MILLISECONDS = 1000

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard_formatter": {
            "format": "[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s]:"
                      " %(message)s",
        },
    },
    "handlers": {},
    "root": {
        "handlers": [],
        "level": "DEBUG"
    },
    "loggers": {
        "__main__": {
            "level": "INFO",
            "propagate": True,
        },
        "translations_server": {
            "level": "INFO",
            "propagate": True,
        },
        "dbquery.db": {
            "level": "INFO",
        },
    },
}


def _override_from_local():
    try:
        __import__("config_local")
    except ImportError:
        pass
    else:
        import config_local as _config_local
        for attr in dir(_config_local):
            module_vars = globals()
            if not attr.startswith("_"):
                module_vars[attr] = getattr(_config_local, attr)


def _check_vars():
    module_vars = globals()
    for attr in module_vars:
        if not attr.startswith("_"):
            if module_vars[attr] is None:
                raise KeyError(attr + " is not set")

_override_from_local()
_check_vars()

# Provides the ability to deactivate Sentry logging on the development and
# testing environment by setting SENTRY_DSN="False"
if SENTRY_DSN not in (False, "False"):
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING  # Send warnings and errors as events
    )
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            sentry_logging,
        ],
        environment=ENVIRONMENT,
    )

# Provides the ability to deactivate file logging on the development
# and testing environment by setting LOGS_LOCATION="False"
if LOGS_LOCATION not in (False, "False"):
    LOGGING["handlers"]["standard_handler"] = {
        "formatter": "standard_formatter",
        "level": "INFO",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOGS_LOCATION + "/log.log",
        "when": "D",
        "interval": 1,
        "backupCount": 10,
        "encoding": "utf-8",
        "delay": False,
        "utc": True
    }
    LOGGING["root"]["handlers"].append("standard_handler")
_dictConfig(LOGGING)

_db_url = _urlparse(TRANSLATIONS_SERVER_DB_URL)
DB_PARAMS = {
    "database": _db_url.path[1:],
    "user": _db_url.username,
    "password": _db_url.password,
    "host": _db_url.hostname
}

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
from datetime import timedelta

from django.forms import Textarea
from django.utils.translation import ugettext_lazy as _

from celery.schedules import crontab

# -----------------------------------------------------------------------------------
# Sets TESTING to True if this configuration is read during a unit test
# -----------------------------------------------------------------------------------
TESTING = sys.argv[1:2] == ["test"]

DEBUG = True
THUMBNAIL_DEBUG = DEBUG

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        "NAME": "dash.sqlite",  # Or path to database file if using sqlite3.
        "USER": "",  # Not used with sqlite3.
        "PASSWORD": "",  # Not used with sqlite3.
        "HOST": "",  # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",  # Set to empty string for default. Not used with sqlite3.
    }
}


SITE_BACKEND = "rtm.backend.rapidpro.RapidProBackend"


# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone
TIME_ZONE = "GMT"
USER_TIME_ZONE = "GMT"
USE_TZ = True

MODELTRANSLATION_TRANSLATION_REGISTRY = "translation"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

# Available languages for translation
LANGUAGES = (
    ("bs", "Bosnian"),
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("ar", "Arabic"),
    ("pt", "Portuguese"),
    ("pt-br", "Brazilian Portuguese"),
    ("uk", "Ukrainian"),
    ("uz", "Uzbek"),
    ("my", "Burmese"),
    ("id", "Indonesian"),
    ("it", "Italian"),
    ("ro", "Romanian"),
    ("vi", "Vietnamese"),
    ("sr-latn", "Latin Serbian"),
)

DEFAULT_LANGUAGE = "en"
RTL_LANGUAGES = ["ar"]

ORG_LANG_MAP = {
    "ar": "ar_AR",
    "en": "en_US",
    "es": "es_ES",
    "fr": "fr_FR",
    "id": "id_ID",
    "it": "it_IT",
    "my": "my_MM",
    "pt": "pt_PT",
    "pt-br": "pt_BR",
    "uk": "uk_UA",
    "vi": "vi_VN",
}


SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/sitestatic/"
COMPRESS_URL = "/sitestatic/"

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = "/sitestatic/admin/"

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

COMPRESS_PRECOMPILERS = (("text/less", "lessc {infile} {outfile}"),)

# Make this unique, and don't share it with anybody.
SECRET_KEY = "your secret key must be here"

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "dash.orgs.middleware.SetOrgMiddleware",
    "rtm.utils.middleware.CheckVersionMiddleware",
)

ROOT_URLCONF = "rtm.urls"


DATA_API_BACKENDS_CONFIG = {
    "rapidpro": {"name": "RapidPro", "slug": "rapidpro", "class_type": "rtm.backend.rapidpro.RapidProBackend"}
}

DATA_API_BACKEND_TYPES = (
    ("rtm.backend.rapidpro.RapidProBackend", "RapidPro Backend Type"),
)


INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # the django admin
    "django.contrib.admin",
    # compress our CSS and js
    "compressor",
    # thumbnail
    "sorl.thumbnail",
    # smartmin
    "smartmin",
    # import tasks
    "smartmin.csv_imports",
    # smartmin users
    "smartmin.users",
    # dash apps
    "dash.orgs",
    "dash.dashblocks",
    "dash.stories",
    "dash.utils",
    "dash.categories",
    # rtm apps
    "rtm.admins",
    "rtm.api",
    "rtm.contacts",
    "rtm.locations",
    "rtm.polls",
    "rtm.stats",
    "django_countries",
    "rest_framework",
    "hamlpy",
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {"console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "verbose"}},
    "loggers": {
        "httprouterthread": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "ERROR"},
    },
}

# -----------------------------------------------------------------------------------
# Directory Configuration
# -----------------------------------------------------------------------------------

PROJECT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))
RESOURCES_DIR = os.path.join(PROJECT_DIR, "../resources")

LOCALE_PATHS = (os.path.join(PROJECT_DIR, "../locale"),)
FIXTURE_DIRS = (os.path.join(PROJECT_DIR, "../fixtures"),)
TESTFILES_DIR = os.path.join(PROJECT_DIR, "../testfiles")
STATICFILES_DIRS = (os.path.join(PROJECT_DIR, "../static"), os.path.join(PROJECT_DIR, "../media"))
STATIC_ROOT = os.path.join(PROJECT_DIR, "../sitestatic")
MEDIA_ROOT = os.path.join(PROJECT_DIR, "../media")
MEDIA_URL = "/media/"


# -----------------------------------------------------------------------------------
# Templates Configuration
# -----------------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_DIR, "../templates")],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "dash.orgs.context_processors.user_group_perms_processor",
                "dash.orgs.context_processors.set_org_processor",
            ],
            "loaders": [
                "dash.utils.haml.HamlFilesystemLoader",
                "dash.utils.haml.HamlAppDirectoriesLoader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "debug": False if TESTING else DEBUG,
        },
    }
]


# -----------------------------------------------------------------------------------
# Permission Management
# -----------------------------------------------------------------------------------

# this lets us easily create new permissions across our objects
PERMISSIONS = {
    "*": (
        "create",  # can create an object
        "read",  # can read an object, viewing it's details
        "update",  # can update an object
        "delete",  # can delete an object,
        "list",
    ),  # can view a list of the objects
    "dashblocks.dashblock": ("html",),
    "orgs.org": ("choose", "edit", "home", "manage_accounts", "create_login", "join", "refresh_cache"),
    "polls.poll": ("questions", "responses", "images", "pull_refresh", "poll_date", "poll_flow"),
    "stories.story": ("html", "images"),
}

# assigns the permissions that each group should have
GROUP_PERMISSIONS = {
    "Administrators": (
        "assets.image.*",
        "categories.category.*",
        "categories.categoryimage.*",
        "dashblocks.dashblock.*",
        "dashblocks.dashblocktype.*",
        "jobs.jobsource.*",
        "news.newsitem.*",
        "news.video.*",
        "orgs.org_edit",
        "orgs.org_home",
        "orgs.org_manage_accounts",
        "orgs.org_profile",
        "polls.poll.*",
        "polls.pollcategory.*",
        "polls.pollimage.*",
        "polls.featuredresponse.*",
        "stories.story.*",
        "stories.storyimage.*",
        "users.user_profile",
    ),
    "Editors": (
        "categories.category.*",
        "categories.categoryimage.*",
        "dashblocks.dashblock.*",
        "dashblocks.dashblocktype.*",
        "jobs.jobsource.*",
        "news.newsitem.*",
        "news.video.*",
        "orgs.org_home",
        "orgs.org_profile",
        "polls.poll.*",
        "polls.pollcategory.*",
        "polls.pollimage.*",
        "polls.featuredresponse.*",
        "stories.story.*",
        "stories.storyimage.*",
        "users.user_profile",
    ),
    "Viewers": ("polls.poll_list",),
    "Global Viewers": ("flowhub.flowhub.*",),
    "Global": ("countries.countryalias.*",),
}


# -----------------------------------------------------------------------------------
# Auth Configuration
# -----------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

ANONYMOUS_USER_NAME = "AnonymousUser"

# -----------------------------------------------------------------------------------
# Redis Configuration
# -----------------------------------------------------------------------------------

# by default, celery doesn't have any timeout on our redis connections, this fixes that
BROKER_TRANSPORT_OPTIONS = {"socket_timeout": 5}

BROKER_BACKEND = "redis"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = "1"

BROKER_URL = "redis://%s:%s/%s" % (REDIS_HOST, REDIS_PORT, REDIS_DB)

CELERY_RESULT_BACKEND = BROKER_URL


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": BROKER_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

if "test" in sys.argv:
    CACHES["default"]["LOCATION"] = "redis://127.0.0.1:6379/15"


# -----------------------------------------------------------------------------------
# Debug Toolbar
# -----------------------------------------------------------------------------------

INTERNAL_IPS = ("127.0.0.1",)

# -----------------------------------------------------------------------------------
# Crontab Settings
# -----------------------------------------------------------------------------------

CELERY_TIMEZONE = "UTC"

CELERYBEAT_SCHEDULE = {
    "refresh_flows": {"task": "polls.refresh_org_flows", "schedule": timedelta(minutes=20), "relative": True},
    "recheck_poll_flow_data": {
        "task": "polls.recheck_poll_flow_data",
        "schedule": timedelta(minutes=15),
        "relative": True,
    },
    "fetch_old_sites_count": {
        "task": "polls.fetch_old_sites_count",
        "schedule": timedelta(minutes=20),
        "relative": True,
    },
    "contact-pull": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": crontab(minute=[0, 10, 20, 30, 40, 50]),
        "args": ("rtm.contacts.tasks.pull_contacts",),
    },
    "backfill-poll-results": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
        "relative": True,
        "args": ("rtm.polls.tasks.backfill_poll_results", "sync"),
    },
    "results-pull-main-poll": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": crontab(minute=[5, 25, 45]),
        "args": ("rtm.polls.tasks.pull_results_main_poll", "sync"),
    },
    "results-pull-recent-polls": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(hours=1),
        "relative": True,
        "args": ("rtm.polls.tasks.pull_results_recent_polls", "sync"),
    },
    "results-pull-brick-polls": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(hours=1),
        "relative": True,
        "args": ("rtm.polls.tasks.pull_results_brick_polls", "sync"),
    },
    "results-pull-other-polls": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(hours=1),
        "relative": True,
        "args": ("rtm.polls.tasks.pull_results_other_polls", "sync"),
    },
    "refresh-engagement-data": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(hours=6),
        "relative": True,
        "args": ("rtm.stats.tasks.refresh_engagement_data", "sync"),
    },
}


RTM_PRIMARY_COLOR = "#FFD100"
RTM_SECONDARY_COLOR = "#1F49BF"


# -----------------------------------------------------------------------------------
# rest_framework config
# -----------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "PAGE_SIZE": 10,  # Default to 10
    "PAGINATE_BY_PARAM": "page_size",  # Allow client to override, using `?page_size=xxx`.
    "MAX_PAGINATE_BY": 100,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "WARNING", "handlers": ["console"]},
    "formatters": {"verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"}},
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"},
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "pycountry": {"level": "ERROR", "handlers": ["console"], "propagate": False},
        "django.security.DisallowedHost": {"handlers": ["null"], "propagate": False},
        "django.db.backends": {"level": "ERROR", "handlers": ["console"], "propagate": False},
    },
}

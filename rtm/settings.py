import dj_database_url
import sentry_sdk

from decouple import config
from sentry_sdk.integrations.django import DjangoIntegration
from rtm.settings_common import *  # noqa


DEBUG = config("DEBUG", default=False, cast=bool)
TEMPLATE_DEBUG = DEBUG

EMPTY_SUBDOMAIN_HOST = config("EMPTY_SUBDOMAIN_HOST", "http://localhost:8000")
HOSTNAME = config("APP_HOSTNAME", "localhost:8000")
SITE_HOST_PATTERN = config("SITE_HOST_PATTERN", default="http://{}.localhost:8000")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=lambda v: [s.strip() for s in v.split(",")])

# SESSION_COOKIE_DOMAIN = config("SESSION_COOKIE_DOMAIN", "localhost:8000")
SESSION_COOKIE_SECURE = False

ADMINS = config(
    "ADMINS",
    default="Ilhasoft|contato@ilhasoft.com.br",
    cast=lambda v: [(s.strip().split("|")[0], s.strip().split("|")[1]) for s in v.split(",")] if v else [],
)
MANAGERS = ADMINS

TIME_ZONE = config("TIME_ZONE", default="America/Sao_Paulo")
USER_TIME_ZONE = config("USER_TIME_ZONE", default="America/Sao_Paulo")

EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", "no-reply@ilhasoft.com.br")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@ilhasoft.com.br")

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")

AWS_S3_SECURE_URLS = False
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

MEDIA_URL = config("MEDIA_URL", default="http://localhost:8000/media/")
SITE_API_HOST = config("SITE_API_HOST", default="https://rapidpro.ilhasoft.mobi")
API_ENDPOINT = config("SITE_API_HOST", default="https://rapidpro.ilhasoft.mobi")

DATABASES = {}
DATABASES["default"] = dj_database_url.parse(config("DEFAULT_DATABASE"))
DATABASES["default"]["CONN_MAX_AGE"] = 0

MIDDLEWARE = MIDDLEWARE + ("whitenoise.middleware.WhiteNoiseMiddleware",)
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REDIS_HOST = config("REDIS_HOST", default="localhost")
REDIS_DATABASE = config("REDIS_DATABASE", default="1")

BROKER_URL = "redis://{}:6379/{}".format(REDIS_HOST, REDIS_DATABASE)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": BROKER_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=BROKER_URL)
CELERY_ALWAYS_EAGER = config("CELERY_ALWAYS_EAGER", default=False, cast=bool)
CELERY_EAGER_PROPAGATES_EXCEPTIONS = config("CELERY_EAGER_PROPAGATES_EXCEPTIONS", default=True, cast=bool)

COMPRESS_ENABLED = config("COMPRESS_ENABLED", default=False, cast=bool)
COMPRESS_OFFLINE = config("COMPRESS_OFFLINE", default=False, cast=bool)
COMPRESS_CSS_FILTERS = ["compressor.filters.css_default.CssAbsoluteFilter", "compressor.filters.cssmin.CSSMinFilter"]
COMPRESS_JS_FILTERS = ["compressor.filters.jsmin.JSMinFilter"]
COMPRESS_CSS_HASHING_METHOD = "content"
COMPRESS_OFFLINE_CONTEXT = dict(STATIC_URL=STATIC_URL, base_template='base.html', debug=False, testing=False)

INSTALLED_APPS += ('gunicorn', 'raven.contrib.django.raven_compat',)

sentry_sdk.init(dsn=config("RAVEN_CONFIG", default=""), integrations=[DjangoIntegration()])

# custom configs
INSTALLED_APPS += (
    "sass_processor",
    "qurl_templatetag",
    "taggit",
    "widget_tweaks",
    "drf_yasg",
    "docs",
    "rtm.uncts",
    "rtm.accounts",
    "rtm.results",
    "rtm.flowhub",
    "rtm.dashboard",
    "rtm.channels",
    "rtm.authentication",
    "rtm.polls_global",
    "rtm.worldmap",
)

SITE_ALLOW_NO_ORG = (
    "dashboard",
    "dashboard_data",
    "flowhub.flow_list",
    "flowhub.flow_uncts",
    "flowhub.flow_create",
    "flowhub.flow_star",
    "flowhub.flow_download",
    "flowhub.flow_info",
    "uncts.unct_create",
    "uncts.unct_list",
    "uncts.unct_update",
    "accounts.user_list",
    "accounts.global_list",
    "accounts.global_user_create",
    "accounts.global_user_update",
    "accounts.global_user_delete",
    "accounts.global_user_activate",
    "accounts.user_org_list",
    "accounts.user_org_create",
    "accounts.user_org_update",
    "accounts.user_org_delete",
    "accounts.user_org_activate",
    "authentication.login",
    "authentication.callback",
    "polls_global.poll_list",
    "polls_global.poll_create",
    "polls_global.poll_update",
    "polls_global.poll_grant",
    "results.poll_read",
    "results.global_poll_read",
    "results.global_poll_data",
    "worldmap.map_list",
    "blocked",
    "results.export_csv",
    "results.global_export_csv",
    "results.export_json",
    "results.global_export_json",
    "docs.login",
    "docs.uncts_users",
    "docs.uncts_repository",
    "docs.uncts_surveys",
    "docs.uncts_dashboard",
    "docs.global_uncts",
    "docs.global_users",
    "docs.global_repository",
    "docs.global_surveys",
    "docs.global_dashboard",
    "results.iframe",
    "uncts.redirect",
    "flowhub.flow_create_global",
    "flowhub.flow_list_global",
    "flowhub.flow_delete",
    "flowhub.flow_update_global"
)

SDG_LIST = (
    (1, "No Poverty"),
    (2, "Zero Hunger"),
    (3, "Good Health and Well-Being"),
    (4, "Quality Education"),
    (5, "Gender Equality"),
    (6, "Clean Water and Sanitation"),
    (7, "Affordable And Clean Energy"),
    (8, "Decent Work and Economic Growth"),
    (9, "Industry, Innovation and Infrastructure"),
    (10, "Reduced Inequalities"),
    (11, "Sustainable Cities and Communities"),
    (12, "Responsible Production and Consumption"),
    (13, "Climate Action"),
    (14, "Life Below Water"),
    (15, "Life On Land"),
    (16, "Peace, Justice and Strong Institutions"),
    (17, "Partnerships for the Goals"),
)

SDG_COLOR = {
    1: "#e3263b",
    2: "#dfa739",
    3: "#4d9f45",
    4: "#c5202e",
    5: "#ef402c",
    6: "#29bee2",
    7: "#f9c316",
    8: "#a21b45",
    9: "#f3692c",
    10: "#dd2467",
    11: "#f99d28",
    12: "#be8b2d",
    13: "#407f45",
    14: "#1c97d3",
    15: "#5ebb47",
    16: "#056a9d",
    17: "#18486a",
}

AVAILABLE_COLORS = [
    "#7bcff6",
    "#03aeef",
    "#0080ca",
    "#004f94",
    "#1F00F5",
    "#02008A",
    "#0300B0",
    "#0400A4",
    "#0400F0",
    "#020063",
    "#2709BD",
    "#1C0B70",
    "#320CF0",
    "#4927F2",
    "#170670",
]

CHANNEL_TYPES = {
    "EX": {"name": "External", "icon": "icon-phone"},
    "TG": {"name": "Telegram", "icon": "icon-telegram"},
    "FB": {"name": "Facebook", "icon": "icon-facebook"},
    "TW": {"name": "Twitter", "icon": "icon-twitter"},
    "KN": {"name": "SMS", "icon": "icon-phone"},
    "WA": {"name": "Whatsapp", "icon": "icon-whatsapp"},
    "FCM": {"name": "Firebase Chat Messaging", "icon": "icon-phone"},
}

STATICFILES_FINDERS += ("sass_processor.finders.CssFinder",)

TOKEN_WORKSPACE_GLOBAL = config("TOKEN_WORKSPACE_GLOBAL", "your token for global workspace in rapidpro")

SASS_PROCESSOR_INCLUDE_FILE_PATTERN = r"^.+\.scss$"

LOGIN_URL = "/users/login/"
LOGOUT_URL = "/users/logout/"
LOGIN_REDIRECT_URL = "/worldmap"
LOGOUT_REDIRECT_URL = "http://dataforallcloud.org/"

CELERYBEAT_SCHEDULE = {
    "refresh_flows": {"task": "polls.refresh_org_flows", "schedule": timedelta(minutes=1), "relative": True},
    "recheck_poll_flow_data": {
        "task": "polls.recheck_poll_flow_data",
        "schedule": timedelta(minutes=1),
        "relative": True,
    },
    "fetch_old_sites_count": {
        "task": "polls.fetch_old_sites_count",
        "schedule": timedelta(minutes=10),
        "relative": True,
    },
    "contact-pull": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
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
        "schedule": timedelta(minutes=10),
        "args": ("rtm.polls.tasks.pull_results_main_poll", "sync"),
    },
    "results-pull-recent-polls": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
        "relative": True,
        "args": ("rtm.polls.tasks.pull_results_recent_polls", "sync"),
    },
    "results-pull-brick-polls": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
        "relative": True,
        "args": ("rtm.polls.tasks.pull_results_brick_polls", "sync"),
    },
    "results-pull-other-polls": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
        "relative": True,
        "args": ("rtm.polls.tasks.pull_results_other_polls", "sync"),
    },
    "refresh-engagement-data": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
        "relative": True,
        "args": ("rtm.stats.tasks.refresh_engagement_data", "sync"),
    },
    "pull-channel-stats": {
        "task": "dash.orgs.tasks.trigger_org_task",
        "schedule": timedelta(minutes=10),
        "relative": True,
        "args": ("rtm.channels.tasks.pull_channel_stats", "sync"),
    },
}


## OAUTH2

OAUTHLIB_CLIENT_ID = config("OAUTHLIB_CLIENT_ID", default="")
OAUTHLIB_SECRET = config("OAUTHLIB_SECRET", default="")
OAUTHLIB_AUTHORIZATION_URL = config(
    "OAUTHLIB_AUTHORIZATION_URL", default="http://dataforallcloud.org/oauth2/authorize"
)
OAUTHLIB_TOKEN_URL = config("OAUTHLIB_TOKEN_URL", default="http://dataforallcloud.org/oauth2/token")
OAUTHLIB_INSECURE_TRANSPORT = config("OAUTHLIB_INSECURE_TRANSPORT", default=False)
OAUTHLIB_REDIRECT_URI = config(
    "OAUTHLIB_REDIRECT_URI", default="https://rtm-ilhasoft.ngrok.io/authentication/callback"
)
OAUTHLIB_USER_URL = config("OAUTHLIB_USER_URL", default="http://dataforallcloud.org/oauth2/userInfo")
OAUTHLIB_MOMSERVICE_TOKEN_URL = config(
    "OAUTHLIB_MOMSERVICE_TOKEN_URL", default="http://dataforallcloud.org/monservice/api/v1/token"
)
OAUTHLIB_MOMSERVICE_USER_URL = config(
    "OAUTHLIB_MOMSERVICE_USER_URL", default="http://dataforallcloud.org/monservice/api/v1/rtmUserInfo"
)
OAUTHLIB_APP_ID = config("OAUTHLIB_APP_ID", default="uninfortm")


#============================================
SECRET_KEY = config("SECRET_KEY", "your secret key must be here")

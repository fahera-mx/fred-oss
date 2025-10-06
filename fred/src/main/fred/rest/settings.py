from fred.settings import get_environ_variable, logger_manager

logger = logger_manager.get_logger(name=__name__)


FRD_RESTAPI_HOST = get_environ_variable(
    "FRD_RESTAPI_HOST",
    default="0.0.0.0"
)
FRD_RESTAPI_PORT = int(get_environ_variable(
    "FRD_RESTAPI_PORT",
    default=8000
))

FRD_RESTAPI_LOGLEVEL = get_environ_variable(
    "FRD_RESTAPI_LOGLEVEL",
    default="info"
).lower()

FRD_RESTAPI_DISABLE_AUTH = get_environ_variable(
    "FRD_RESTAPI_DISABLE_AUTH",
    default="false"
).lower() in ("1", "true", "yes", "on")

FRD_RESTAPI_TOKEN = get_environ_variable(
    "FRD_RESTAPI_TOKEN",
    default=None
)
if not FRD_RESTAPI_TOKEN:
    logger.warning("FRD_RESTAPI_TOKEN not found in environment; using default token 'changeme'.")
    FRD_RESTAPI_TOKEN = "changeme"

FRD_RESTAPI_EXCLUDE_BUILTIN_ROUTERS = get_environ_variable(
    "FRD_RESTAPI_EXCLUDE_BUILTIN_ROUTERS",
    default="false",
).lower() in ("1", "true", "yes", "on")

FRD_RESTAPI_ROUTERCATALOG_CLASSNAME = get_environ_variable(
    "FRD_RESTAPI_ROUTERCATALOG_CLASSNAME",
    default="RouterCatalog",
)

FRD_RESTAPI_ROUTERCATALOG_CLASSPATH = get_environ_variable(
    "FRD_RESTAPI_ROUTERCATALOG_CLASSPATH",
    default="fred.rest.router.catalog.default",
)

from fred.settings import get_environ_variable, logger_manager

logger = logger_manager.get_logger(name=__name__)


FRD_RESTAPI_TOKEN = get_environ_variable(
    "FRD_RESTAPI_TOKEN",
    default=None
)
if not FRD_RESTAPI_TOKEN:
    logger.warning("FRD_RESTAPI_TOKEN not found in environment; using default token 'changeme'.")
    FRD_RESTAPI_TOKEN = "changeme"

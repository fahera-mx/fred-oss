from fred.rest.router.catalog.default.catalog import RouterCatalog
from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


logger.warning(
    "You are using the default router catalog inteded for demonstration purposes only. "
    "For production use, please implement a custom router catalog."
)

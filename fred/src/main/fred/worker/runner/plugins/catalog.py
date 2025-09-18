import enum
from dataclasses import dataclass

from fred.settings import logger_manager
from fred.worker.runner.plugins._local import LocalPlugin

logger = logger_manager.get_logger(name=__name__)


class PluginCatalog(enum.Enum):
    """Enum for the different plugins available in FRED."""

    LOCAL = LocalPlugin.auto()
    RUNPOD = None  # Placeholder for future RunPod plugin
    LAMBDA = None  # Placeholder for future AWS Lambda plugin

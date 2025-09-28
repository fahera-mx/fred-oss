import enum
from dataclasses import dataclass

from fred.settings import logger_manager
from fred.worker.runner.plugins._local import LocalPlugin
from fred.worker.runner.plugins._runpod import RunpodPlugin

logger = logger_manager.get_logger(name=__name__)


class PluginCatalog(enum.Enum):
    """Enum for the different plugins available in FRED."""

    LOCAL = LocalPlugin
    RUNPOD = RunpodPlugin
    LAMBDA = None  # Placeholder for future AWS Lambda plugin

    def __call__(self, *args, **kwargs):
        return self.value.auto(*args, **kwargs)

from fred.version import version
from fred.settings import logger_manager
from fred.cli.interface import AbstractCLI


logger = logger_manager.get_logger(name=__name__)


class CLIExtensionGroups:
    """CLI Extensions providing access to various integrations by following a lazy loading pattern."""

    @property
    def databricks(self):
        from fred.integrations.databricks.cli_ext import DatabricksExt
        return DatabricksExt()
    
    @property
    def runpod(self):
        from fred.integrations.runpod.cli_ext import RunPodExt
        return RunPodExt()


class CLI(AbstractCLI, CLIExtensionGroups):

    def version(self) -> str:
        return version.value

from typing import Optional

from fred.version import version
from fred.settings import logger_manager
from fred.cli.interface import AbstractCLI


logger = logger_manager.get_logger(name=__name__)


class CLI(AbstractCLI):

    def version(self) -> str:
        return version.value

    def sync_databricks_runtime(self, runtime: Optional[str] = None):
        from fred.databricks.runtimes.sync import DatabricksRuntimeSyncHelper

        sync_helper = DatabricksRuntimeSyncHelper.default()
        match runtime:
            case None:
                logger.info("No runtime specified; skipping synchronization.")
            case "all":
                logger.info("Syncing all available Databricks runtimes.")
                sync_helper.sync_all()
            case runtime_name if isinstance(runtime_name, str):
                logger.info(f"Syncing specified Databricks runtime: {runtime_name}")
                sync_helper.sync(runtime=runtime_name)
            case _:
                raise ValueError(f"Invalid runtime value: {runtime}")

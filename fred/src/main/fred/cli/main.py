from typing import Optional

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
    
    @property
    def runner_server(self):
        from fred.worker.runner.rest.cli_ext import RunnerServerExt
        return RunnerServerExt()


class CLI(AbstractCLI, CLIExtensionGroups):

    def version(self) -> str:
        return version.value

    def serve(
            self,
            classname: Optional[str] = None,
            classpath: Optional[str] = None,
            include_routers: Optional[list[str]] = None,
            exclude_routers: Optional[list[str]] = None,
            fastapi_configs: Optional[dict] = None,
            server_configs: Optional[dict] = None,
    ):
        from fred.rest.server import FredServer

        include_routers = include_routers or []
        exclude_routers = exclude_routers or []
        fastapi_configs = fastapi_configs or {}
        server_configs = server_configs or {}

        logger.info("Starting the Fred-REST Server...")
        server = FredServer.auto(
            include_routers=include_routers,
            exclude_routers=exclude_routers,
            router_classname=classname,
            router_classpath=classpath,
            **fastapi_configs,
        )
        server.start(**server_configs)

from typing import Optional

from fred.cli.interface import IntegrationExtCLI
from fred.settings import logger_manager


logger = logger_manager.get_logger(name=__name__)


class RunnerServerExt(IntegrationExtCLI):

    def start(
            self,
            include_routers: Optional[list[str]] = None,
            exclude_routers: Optional[list[str]] = None,
            fast_api_configs: Optional[dict] = None,
            server_configs: Optional[dict] = None,
        ):
        from fred.worker.runner.rest.server import RunnerServer

        include_routers = include_routers or []
        exclude_routers = exclude_routers or []
        fast_api_configs = fast_api_configs or {}
        server_configs = server_configs or {}

        logger.info("Starting REST server...")
        server = RunnerServer.auto(
            include_routers=include_routers,
            exclude_routers=exclude_routers,
            **fast_api_configs,
        )
        server.start(**server_configs)

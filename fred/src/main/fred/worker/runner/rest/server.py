from dataclasses import dataclass

from fastapi import FastAPI

from fred.settings import logger_manager, get_environ_variable
from fred.worker.runner.rest.routers.catalog import RouterCatalog

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RunnerServer:
    app: FastAPI
    include_routers: list[str]
    exclude_routers: list[str]

    @classmethod
    def auto(cls, **kwargs) -> "RunnerServer":
        include_routers = [
            name.upper()
            for name in kwargs.pop(
                "include_routers",
                get_environ_variable("FRD_RUNNER_API_INCLUDE_ROUTERS", default="").split(";"),
            )
        ]
        exclude_routers = [
            name.upper()
            for name in kwargs.pop(
                "exclude_routers",
                get_environ_variable("FRD_RUNNER_API_EXCLUDE_ROUTERS", default="").split(";"),
            )
        ]
        app_instance = FastAPI(**kwargs)
        return cls(
            app=app_instance,
            include_routers=include_routers,
            exclude_routers=exclude_routers,
        )

    def __post_init__(self):
        for router in RouterCatalog:
            name = router.name
            if self.include_routers and name not in self.include_routers:
                logger.info(f"Skipping router '{name}' as it's not in the include list.")
                continue
            if self.exclude_routers and name in self.exclude_routers:
                logger.info(f"Skipping router '{name}' as it's in the exclude list.")
                continue
            logger.info(f"Registering router '{name}'.")
            self.app.include_router(
                router.get_router_instance(),
                **router.get_router_configs(),
            ) 

    def start(self, **kwargs):
        import uvicorn

        server_kwargs = {
            "host": "localhost",
            "port": 8000,
            "log_level": "info",
            **kwargs,
        }

        uvicorn.run(self.app, **server_kwargs)

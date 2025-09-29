from dataclasses import dataclass

from fastapi import FastAPI, Depends

from fred.settings import logger_manager, get_environ_variable
from fred.worker.runner.rest.settings import (
    FRD_RESTAPI_HOST,
    FRD_RESTAPI_PORT,
)
from fred.worker.runner.rest.routers.catalog import RouterCatalog
from fred.worker.runner.rest.auth import verify_key

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RunnerServer:
    app: FastAPI
    include_routers: list[str]
    exclude_routers: list[str]

    @classmethod
    def auto(cls, **kwargs) -> "RunnerServer":
        # Include routers by checking on keyword argument or environment variable
        include_routers = kwargs.pop("include_routers", None) or get_environ_variable(
            "FRD_RUNNER_API_INCLUDE_ROUTERS",
            default=""
        )
        if isinstance(include_routers, str):
            include_routers = [
                name.upper()
                for router in include_routers.split(";")
                if (name := router.strip())
            ]
        # Exclude routers by checking on keyword argument or environment variable
        exclude_routers = kwargs.pop("exclude_routers", None) or get_environ_variable(
            "FRD_RUNNER_API_EXCLUDE_ROUTERS",
            default=""
        )
        if isinstance(exclude_routers, str):
            exclude_routers = [
                name.upper()
                for router in exclude_routers.split(";")
                if (name := router.strip())
            ]
        # Create FastAPI instance
        kwargs["dependencies"] = kwargs.get("dependencies", []) + [
            Depends(verify_key),
        ]
        app_instance = FastAPI(**kwargs)
        return cls(
            app=app_instance,
            include_routers=include_routers,
            exclude_routers=exclude_routers,
        )

    def __post_init__(self):
        logger.info("Attempting to register routers...")
        logger.info("Included routers candidates: %s", self.include_routers or "ALL")
        logger.info("Excluded routers candidates: %s", self.exclude_routers or "NONE")
        for router in RouterCatalog:
            name = router.name.upper()
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
            "host": kwargs.pop("host", FRD_RESTAPI_HOST),
            "port": int(kwargs.pop("port", FRD_RESTAPI_PORT)),
            "log_level": "info",
            **kwargs,
        }

        uvicorn.run(self.app, **server_kwargs)

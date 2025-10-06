from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, Depends

from fred.settings import (
    get_environ_variable,
    logger_manager,
)
from fred.rest.settings import (
    FRD_RESTAPI_HOST,
    FRD_RESTAPI_PORT,
    FRD_RESTAPI_LOGLEVEL,
    FRD_RESTAPI_DISABLE_AUTH,
)
from fred.rest.config import ServerRouterCatalogConfig
from fred.rest.auth import verify_key

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class FredServer:
    app: FastAPI
    include_routers: list[str]
    exclude_routers: list[str]
    router_classname: Optional[str] = None
    router_classpath: Optional[str] = None

    @classmethod
    def auto(cls, **kwargs) -> "FredServer":
        # Include routers by checking on keyword argument or environment variable
        include_routers = kwargs.pop("include_routers", None) or get_environ_variable(
            "FRD_RESTAPI_INCLUDE_ROUTERS",
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
            "FRD_RESTAPI_EXCLUDE_ROUTERS",
            default=""
        )
        if isinstance(exclude_routers, str):
            exclude_routers = [
                name.upper()
                for router in exclude_routers.split(";")
                if (name := router.strip())
            ]
        # Auth dependencies setup
        auth_dependency = [] if FRD_RESTAPI_DISABLE_AUTH else [
            Depends(verify_key),
        ]
        kwargs["dependencies"] = kwargs.get("dependencies", []) + auth_dependency
        # Create FastAPI app instance
        app_instance = FastAPI(**kwargs)
        router_classname = kwargs.pop("router_classname", None)
        router_classpath = kwargs.pop("router_classpath", None)
        return cls(
            app=app_instance,
            include_routers=include_routers,
            exclude_routers=exclude_routers,
            router_classname=router_classname,
            router_classpath=router_classpath,
        )

    def __post_init__(self):
        logger.info("Attempting to register routers...")
        logger.info("Included routers candidates: %s", self.include_routers or "ALL")
        logger.info("Excluded routers candidates: %s", self.exclude_routers or "NONE")
        srcc = ServerRouterCatalogConfig.auto(
            classname=self.router_classname,
            classpath=self.router_classpath,
        )
        for router_spec in srcc.catalog:
            name = router_spec.name.upper()
            if self.include_routers and name not in self.include_routers:
                logger.info(f"Skipping router '{name}' as it's not in the include list.")
                continue
            if self.exclude_routers and name in self.exclude_routers:
                logger.info(f"Skipping router '{name}' as it's in the exclude list.")
                continue
            logger.info(f"Registering router '{name}'.")
            kwargs = router_spec.get_kwargs()
            router_instance = router_spec.value.reference.auto(**kwargs)
            router_configs = router_spec.value.config.get_configs()
            # Register the router in the FastAPI app
            self.app.include_router(router_instance.router, **router_configs) 

    def start(self, **kwargs):
        import uvicorn

        server_kwargs = {
            "host": kwargs.pop("host", FRD_RESTAPI_HOST),
            "port": int(kwargs.pop("port", FRD_RESTAPI_PORT)),
            "log_level": FRD_RESTAPI_LOGLEVEL,
            **kwargs,
        }

        uvicorn.run(self.app, **server_kwargs)

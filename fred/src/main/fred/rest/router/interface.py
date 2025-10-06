from dataclasses import dataclass
from typing import Callable, Optional

from fred.worker.runner.backend import RunnerBackend
from fred.worker.runner.settings import FRD_RUNNER_BACKEND
from fred.rest.router.endpoint import RouterEndpoint
from fred.settings import logger_manager

from fastapi import APIRouter

logger = logger_manager.get_logger(name=__name__)


class RouterInterfaceMixin:
    """Base class for router interfaces that require a backend service."""
    runner_backend: RunnerBackend


@dataclass(frozen=True, slots=True)
class RouterInterface(RouterInterfaceMixin):
    router: APIRouter

    @classmethod
    def set_backend(
            cls,
            service_name: Optional[str] = None,
            disable_runner_reuse: bool = False,
            **kwargs
        ) -> type["RouterInterface"]:
        runner_backend = kwargs.pop("runner_backend", None)
        if not disable_runner_reuse and runner_backend is None:
            logger.warning(
                "Runner reuse is enabled but no existing backend was provided; "
                "a new backend will be created."
            )
            disable_runner_reuse = True
        if disable_runner_reuse:
            runner_backend = RunnerBackend.auto(
                service_name=service_name or FRD_RUNNER_BACKEND,
                **kwargs,
            )
        if runner_backend is None:
            raise ValueError("Runner backend could not be determined or created.")
        return type(
            "RouterInterfaceWithBackend",
            (cls, ),
            {
                "runner_backend": runner_backend
            }
        ) 

    @classmethod
    def auto(
        cls,
        service_name: Optional[str] = None,
        router: Optional[APIRouter] = None,
        disregard_backend: bool = False,
        disregard_endpoint_setup: bool = False,
        **kwargs,
    ) -> "RouterInterface":
        subcls = cls if disregard_backend else cls.set_backend(
            service_name=service_name,
            runner_backend=getattr(cls, "runner_backend", None),
            **kwargs
        )
        instance = subcls(router=router or APIRouter())
        if disregard_endpoint_setup:
            return instance
        for endpoint in subcls.endpoint_definitions():
            instance.register_endpoint(endpoint)
        return instance

    def register_endpoint(self, endpoint: RouterEndpoint, path: Optional[str] = None):
        route_config = endpoint.route_config(path=path)
        self.router.add_api_route(endpoint=endpoint.function, **route_config)

    @classmethod
    def endpoint_definitions(cls) -> list[RouterEndpoint]:
        return [
            obj
            for attr in dir(cls)
            if isinstance((obj := getattr(cls, attr)), RouterEndpoint)
        ]
    
    @classmethod
    def endpoint_definition_mapping(cls) -> dict[str, RouterEndpoint]:
        return {
            endpoint.get_path(): endpoint
            for endpoint in cls.endpoint_definitions()
        }

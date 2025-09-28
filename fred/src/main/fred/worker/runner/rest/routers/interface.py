from dataclasses import dataclass
from typing import Optional

from fred.worker.runner.backend import RunnerBackend
from fred.worker.runner.settings import FRD_RUNNER_BACKEND

from fastapi import APIRouter


class RouterInterfaceBackendMixin:
    """Base class for router interfaces that require a backend service."""
    runner_backend: RunnerBackend

    @classmethod
    def with_backend(cls, service_name: Optional[str] = None, **kwargs) -> type["RouterInterfaceBackendMixin"]:
        # Avoid re-initializing if already set
        if getattr(cls, "runner_backend", None):
            return cls
        # Initialize the backend once and assign to the class attribute
        cls.runner_backend = RunnerBackend.auto(
            service_name=service_name or FRD_RUNNER_BACKEND,
            **kwargs,
        )
        return cls


@dataclass(frozen=True, slots=False)
class RouterInterface(RouterInterfaceBackendMixin):
    router: APIRouter
    router_configs: dict

    @classmethod
    def auto(
        cls,
        router: Optional[APIRouter] = None,
        **kwargs,
    ) -> "RouterInterface":
        return cls(
            router=router or APIRouter(),
            router_configs=kwargs,
        )

    def __post_init__(self):
        self.router.add_api_route(
            "/ping",
            self.ping,
            methods=["GET"],
            tags=["Health"],
            summary="Ping the server to check if it's alive.",
            response_description="A simple pong response.",
        )

    def ping(self, pong: Optional[str] = None) -> dict:
        from fred.utils.dateops import datetime_utcnow

        return {
            "ping_time": datetime_utcnow().isoformat(),
            "ping_response": pong or "pong",
        }

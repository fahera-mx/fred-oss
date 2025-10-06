from dataclasses import dataclass
from typing import Optional

from fred.rest.router.interface import RouterInterface
from fred.rest.router.endpoint import RouterEndpointAnnotation


class RouterExampleMixin:

    @RouterEndpointAnnotation.set(
        path="/ping",
        methods=["GET"],
        summary="Ping endpoint",
        description="A simple ping endpoint to check service availability.",
    )
    def ping(self, pong: Optional[str] = None, **kwargs) -> dict:
        from fred.utils.dateops import datetime_utcnow

        return {
            "ping_time": datetime_utcnow().isoformat(),
            "ping_response": pong or "pong",
        }

    @RouterEndpointAnnotation.set(
        path="/passthrough",
        methods=["GET"],
        summary="Passthrough GET endpoint",
        description="An endpoint that returns all received parameters.",
    )
    def passthrough(self, **kwargs) -> dict:
        return kwargs


@dataclass(frozen=True, slots=True)
class RouterExample(RouterInterface, RouterExampleMixin):
    pass

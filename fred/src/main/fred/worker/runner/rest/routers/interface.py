from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter


@dataclass(frozen=True, slots=False)
class RouterInterface:
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

import enum

from fred.worker.runner.rest.routers.interface import RouterInterface
from fred.worker.runner.rest.routers._runner import RunnerRouter


class RouterCatalog(enum.Enum):
    EXAMPLE = RouterInterface.auto()  # Default example router directly from the base interface
    RUNNER = RunnerRouter.auto(
        prefix="/runner",
        tags=["Runner"],
    )

    def get_router_instance(self) -> RouterInterface:
        return self.value.router

    def get_router_configs(self) -> dict:
        return self.value.router_configs

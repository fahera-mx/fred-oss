import enum

from fred.rest.router.config import RouterConfig
from fred.rest.router.catalog.interface import RouterCatalogInterface
from fred.worker.runner.rest.routers._runner import RunnerRouterMixin
from fred.worker.runner.rest.routers._base import RouterBaseMixin


class RouterCatalog(RouterCatalogInterface, enum.Enum):
    BASE = RouterConfig.auto(prefix="")(apply=RouterBaseMixin)
    RUNNER = RouterConfig.auto(prefix="/runner", tags=["Runner"])(apply=RunnerRouterMixin)

import enum

from fred.rest.router.config import RouterConfig
from fred.rest.router.catalog.default._base import RouterBaseMixin
from fred.rest.router.catalog.default._example import RouterExampleMixin

from fred.rest.router.catalog.interface import RouterCatalogInterface


class RouterCatalog(RouterCatalogInterface, enum.Enum):
    BASE = RouterConfig.auto(prefix="")(apply=RouterBaseMixin)
    EXAMPLE = RouterConfig.auto(prefix="/example")(apply=RouterExampleMixin)

    def get_kwargs(self) -> dict:
        match self:
            case RouterCatalog.EXAMPLE:
                # Disable the backend for the example router
                return {"disregard_backend": True}
            case _:
                return {}

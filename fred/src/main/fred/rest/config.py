from dataclasses import dataclass
from typing import Optional

from fred.rest.router.catalog.interface import RouterCatalogInterface
from fred.rest.settings import (
    FRD_RESTAPI_ROUTERCATALOG_CLASSPATH,
    FRD_RESTAPI_ROUTERCATALOG_CLASSNAME,
)

@dataclass(frozen=True, slots=True)
class ServerRouterCatalogConfig:
    classname: str
    classpath: str

    @classmethod
    def auto(cls, classname: Optional[str] = None, classpath: Optional[str] = None) -> "ServerRouterCatalogConfig":
        return cls(
            classname=classname or FRD_RESTAPI_ROUTERCATALOG_CLASSNAME,
            classpath=classpath or FRD_RESTAPI_ROUTERCATALOG_CLASSPATH,
        )

    @property
    def catalog(self) -> type[RouterCatalogInterface]:
        import importlib

        module = importlib.import_module(self.classpath)
        catalog_class = getattr(module, self.classname, None)
        if catalog_class is None:
            raise ImportError(f"Could not find class '{self.classname}' in module '{self.classpath}'")
        if not issubclass(catalog_class, RouterCatalogInterface):
            raise TypeError(f"Class '{self.classname}' is not a subclass of RouterCatalogInterface")
        return catalog_class

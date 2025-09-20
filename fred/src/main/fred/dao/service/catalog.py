import enum
from functools import lru_cache

from fred.dao.service.interface import ServiceInterface
from fred.dao.service._redis import RedisService


class ServiceCatalog(enum.Enum):
    REDIS = RedisService

    @classmethod
    def from_classname(cls, classname: str) -> "ServiceCatalog":
        for item in cls:
            if item.value.__name__ == classname:
                return item
        raise ValueError(f"No service found for classname: {classname}")

    @lru_cache
    def component_catalog(self, **kwargs) -> enum.Enum:
        """Get a preconfigured component catalog for this (self) service.
        This method returns a new Enum with preconfigured components for the
        service represented by this enum member.
        Args:
            **kwargs: Additional keyword arguments to pass to the component constructors.
        Returns:
             enum.Enum: A new Enum with preconfigured components for this service.
        """
        from fred.dao.comp.catalog import CompCatalog  # Avoid circular import

        return CompCatalog.preconf(srv_name=self.name, **kwargs)

    def service_cls(self) -> type[ServiceInterface]:
        return self.value

    def auto(self, **kwargs) -> ServiceInterface:
        return self.value.auto(**kwargs)

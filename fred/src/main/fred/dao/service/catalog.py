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

    def service_cls(self) -> type[ServiceInterface]:
        return self.value

    def auto(self, **kwargs) -> ServiceInterface:
        return self.value.auto(**kwargs)

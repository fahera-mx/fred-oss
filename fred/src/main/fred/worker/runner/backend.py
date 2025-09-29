from dataclasses import dataclass

from fred.settings import logger_manager
from fred.dao.comp.catalog import FredKeyVal, FredQueue
from fred.dao.service.catalog import ServiceCatalog

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=False)
class RunnerBackend:
    keyval: FredKeyVal
    queue: FredQueue
    _cat: ServiceCatalog

    @classmethod
    def auto(cls, service_name: str, **kwargs) -> 'RunnerBackend':
        service = ServiceCatalog[service_name.upper()]
        match service:
            case ServiceCatalog.REDIS:
                from fred.dao.service.utils import get_redis_configs_from_payload
                service_kwargs = get_redis_configs_from_payload(kwargs)
            case ServiceCatalog.STDLIB:
                service_kwargs = {}
            case _:
                logger.error(f"Unknown service '{service_name}'... will attempt to use provided kwargs as-is.")
                service_kwargs = kwargs
        components = service.component_catalog(**service_kwargs)
        return cls(
            keyval=components.KEYVAL.value,
            queue=components.QUEUE.value,
            _cat=service,
        )

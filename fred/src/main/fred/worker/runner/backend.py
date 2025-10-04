from dataclasses import dataclass

from fred.settings import logger_manager
from fred.dao.comp.catalog import FredKeyVal, FredQueue, CompCatalog
from fred.dao.service.interface import ServiceInterface
from fred.dao.service.catalog import ServiceCatalog

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=False)
class RunnerBackend:
    keyval: FredKeyVal
    queue: FredQueue
    # NOTE: Catalog and service instance references (for internal use)
    # should be a temporal fix until we refactor the backend system
    # according to a more precise usage-patter (still to be defined/identified).
    _cat: ServiceCatalog  # Contains complementary service info and simple references
    _srv: ServiceInterface  # Allows direct access to a client instance

    @classmethod
    def auto(cls, service_name: str, **kwargs) -> 'RunnerBackend':
        match (srv_catalog := ServiceCatalog[service_name.upper()]):
            case ServiceCatalog.REDIS:
                from fred.dao.service.utils import get_redis_configs_from_payload
                service_kwargs = get_redis_configs_from_payload(kwargs)
            case ServiceCatalog.STDLIB:
                service_kwargs = {}
            case _:
                logger.error(
                    f"Unknown service '{service_name}'... "
                    "will attempt to use provided kwargs as-is."
                )
                service_kwargs = kwargs
        logger.info(f"Initializing RunnerBackend using service '{service_name}'")
        srv_instance = srv_catalog.auto(**service_kwargs)
        return cls(
            keyval=CompCatalog.KEYVAL.value.mount(srv_ref=srv_instance),
            queue=CompCatalog.QUEUE.value.mount(srv_ref=srv_instance),
            _cat=srv_catalog,
            _srv=srv_instance,
        )

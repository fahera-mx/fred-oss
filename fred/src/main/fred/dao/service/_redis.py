from redis import Redis, ConnectionPool

from fred.dao.service.utils import get_redis_configs_from_payload
from fred.dao.service.interface import ServiceConnectionPoolInterface, ServiceInterface


class RedisConnectionPool(ServiceConnectionPoolInterface[ConnectionPool]):

    @classmethod
    def _create_pool(cls, **kwargs) -> ConnectionPool:
        configs = get_redis_configs_from_payload(payload=kwargs, keep=False)
        return ConnectionPool(**configs)


class RedisService(ServiceInterface[Redis]):
    instance: Redis

    @classmethod
    def _create_instance(cls, **kwargs) -> Redis:
        return Redis(connection_pool=RedisConnectionPool.get_or_create_pool(**kwargs))

    @classmethod
    def auto(cls, **kwargs) -> "RedisService":
        cls.instance = Redis(connection_pool=RedisConnectionPool.get_or_create_pool(**kwargs))
        return cls(**kwargs)

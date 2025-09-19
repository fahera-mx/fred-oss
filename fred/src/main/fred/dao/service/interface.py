import uuid
import json
from functools import lru_cache
from typing import Generic, TypeVar

T = TypeVar("T")


class ServiceConnectionPoolInterface(Generic[T]):
    pool_registry: dict[str, T] = {}

    @classmethod
    def get_pool_id(cls, **kwargs) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(kwargs, sort_keys=True)))

    @classmethod
    def _create_pool(cls, **kwargs) -> T:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @classmethod
    @lru_cache
    def get_or_create_pool(cls, **kwargs) -> T:
        pool_id = cls.get_pool_id(**kwargs)
        pool = cls.pool_registry.get(pool_id)
        if not pool:
            pool = cls.pool_registry[pool_id] = cls._create_pool(**kwargs)
        return pool


class ServiceInterface(Generic[T]):
    instance: T

    def __init__(self, **kwargs):
        self.config = kwargs

    @classmethod
    def _create_instance(cls, **kwargs) -> T:
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @classmethod
    def auto(cls, **kwargs) -> "ServiceInterface":
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    def client(self) -> T:  
        if not getattr(self, "instance", None):
            self.instance = self._create_instance(**getattr(self, "config", {}))
        return self.instance
    
    def close(self):
        # Close the instance if it has a close method.
        # This method can be overridden by subclasses if needed.
        if self.instance and hasattr(self.instance, "close") and callable(self.instance.close):
            self.instance.close()

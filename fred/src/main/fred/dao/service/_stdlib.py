from queue import Queue
from dataclasses import dataclass
from typing import Optional

from fred.utils.runtime import RuntimeInfo
from fred.dao.service.interface import ServiceConnectionPoolInterface, ServiceInterface


class StdLibSingleton:
    _instance: Optional["StdLib"] = None

    @classmethod
    def get_instance(cls, **kwargs) -> "StdLib":
        if cls._instance is None:
            cls._instance = StdLib.auto(**kwargs)
        return cls._instance


@dataclass(frozen=True, slots=True)
class StdLib:
    runtime_info: RuntimeInfo
    _memstore_keyval: dict[str, str]
    _memstore_queue: dict[str, Queue]

    @classmethod
    def auto(cls, **kwargs) -> "StdLib":
        _memstore_keyval = kwargs.pop("memstore_keyval", {})
        _memstore_queue = kwargs.pop("memstore_queue", {})
        return cls(
            runtime_info=RuntimeInfo.auto(**kwargs),
            _memstore_keyval=_memstore_keyval,
            _memstore_queue=_memstore_queue,
        )


class StdLibConnectionPool(ServiceConnectionPoolInterface[StdLibSingleton]):

    @classmethod
    def _create_pool(cls, **kwargs) -> StdLibSingleton:
        return StdLibSingleton(**kwargs)


class StdLibService(ServiceInterface[StdLib]):
    instance: StdLib

    @classmethod
    def _create_instance(cls, **kwargs) -> StdLib:
        pool = StdLibConnectionPool.get_or_create_pool(**kwargs)
        return pool.get_instance(**kwargs)

    @classmethod
    def auto(cls, **kwargs) -> "StdLib":
        cls.instance = cls._create_instance(**kwargs)
        return cls(**kwargs)

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional

from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


# Note: We need to turn off frozen & slots here to allow dynamic attribute setting
# by the wraps decorator
@dataclass(frozen=False, slots=False)
class DBUtilsRetrievalMethod:
    position: int
    function: Callable

    @classmethod
    def with_position(cls, value: int) -> Callable:
        def decorator(function: Callable) -> 'DBUtilsRetrievalMethod':
            instance = cls(position=value, function=function)
            wraps(function)(instance)
            return instance
        return decorator

    def __call__(self, *args, **kwargs) -> Callable:
        return self.function(*args, **kwargs)


@dataclass(frozen=False, slots=True)
class DBUtilsFinder:
    instance: Optional[Any] = None

    
    @staticmethod
    @DBUtilsRetrievalMethod.with_position(value=0)
    def get_dbutils_from_python_context(**kwargs):
        try:
            return (
                locals().get("dbutils")
                or globals().get("dbutils")
            )
        except Exception as e:
            logger.warning(f"Failed to get dbutils from python context: {e}")
            return None

    @staticmethod
    @DBUtilsRetrievalMethod.with_position(value=1)
    def get_dbutils_from_sdk_context(**kwargs):
        try:
            from databricks.sdk.runtime import dbutils
            return dbutils
        except ImportError:
            from databricks.sdk.runtime import get_dbutils
            return get_dbutils()
        except Exception as e:
            logger.warning(f"Failed to get dbutils from SDK context: {e}")
            return None

    @staticmethod
    @DBUtilsRetrievalMethod.with_position(value=2)
    def get_dbutils_from_workspace_client(client: Optional['WorkspaceClient'] = None, **kwargs):
        try:
            if client is None:
                from databricks.sdk import WorkspaceClient
                client = WorkspaceClient()
            return client.dbutils
        except Exception as e:
            logger.warning(f"Failed to get dbutils from workspace client: {e}")
            return None
        
    @staticmethod
    @DBUtilsRetrievalMethod.with_position(value=3)
    def get_dbutils_from_pypspark_import(spark: Optional['SparkSession'] = None, **kwargs):
        try:
            from pyspark.dbutils import DBUtils  # type: ignore[import]
            return DBUtils(spark)
        except Exception as e:
            logger.warning(f"Failed to get dbutils from pyspark context: {e}")
            return None
        
    @staticmethod
    @DBUtilsRetrievalMethod.with_position(value=4)
    def get_dbutils_from_jvm_context(spark: Optional['SparkSession'] = None, **kwargs):
        try:
            if spark is None:
                from pyspark.sql import SparkSession
                spark = SparkSession.builder.getOrCreate()
            return spark._jvm.dbutils
        except Exception as e:
            logger.warning(f"Failed to get dbutils from JVM context: {e}")
            return None
        
    @classmethod
    def find_dbutils(
        cls,
        spark: Optional['SparkSession'] = None,
        client: Optional['WorkspaceClient'] = None,
        start_with_index: int = 0,
    ):
        get_dbutils_methods = sorted(
            [
                method
                for method in dir(cls)
                if method.startswith("get_dbutils_from_")
            ],
            key=lambda m: getattr(cls, m).position
        )

        def try_methods(methods: list[str], index: int = 0):
            # Early exit if index is out of bounds
            if index >= len(methods):
                return None
            # Recursively try each method until one succeeds or we run out of options
            get_dbutils_method, *others = methods[index:]
            if (dbutils := getattr(cls, get_dbutils_method)(spark=spark, client=client)):
                return dbutils
            return try_methods(others, index + 1) if others else None

        return try_methods(methods=get_dbutils_methods, index=start_with_index)
    
    def get(self, **kwargs):
        if self.instance:
            return self.instance
        self.instance = self.find_dbutils(**kwargs)
        return self.instance
    

@dataclass(frozen=True, slots=True)
class DBUtilsWrapper:
    instance: Optional[Any] = None

    @classmethod
    def auto(
        cls,
        spark: Optional['SparkSession'] = None,
        client: Optional['WorkspaceClient'] = None,
        start_with_index: int = 0,
    ) -> 'DBUtilsWrapper':
        return cls(
            instance=DBUtilsFinder.find_dbutils(
                spark=spark,
                client=client,
                start_with_index=start_with_index,
            )
        )

from minio import Minio
from urllib3 import PoolManager, Retry
from urllib3.util import Timeout

from fred.settings import get_environ_variable, logger_manager
from fred.dao.service.utils import get_minio_from_payload
from fred.dao.service.interface import ServiceInterface, ServiceConnectionPoolInterface

logger = logger_manager.get_logger(name=__name__)


class MinioConnectionPool(ServiceConnectionPoolInterface[PoolManager]):

    @classmethod
    def _create_pool(cls, disable_cert: bool = False, **kwargs) -> PoolManager:
        """Create a urllib3 PoolManager with the given configurations.

        TODO: Consider using the inverse of 'require_cert' as the default to ensure we do have cert-check automatically.
        For now, we keep it as is to avoid breaking changes.

        Args:
            require_cert (bool): Whether to require SSL certificate verification.
            **kwargs: Additional keyword arguments to pass to the PoolManager constructor.
        Returns:
            PoolManager: A configured PoolManager instance.
        """
        num_pools = kwargs.pop("num_pools", 10)
        maxsize = kwargs.pop("maxsize", 10)
        # Default timeout of 5 minutes
        timeout_seconds = kwargs.pop("timeout", 300)
        timeout = Timeout(
            connect=timeout_seconds,
            read=timeout_seconds,
        )
        # Default retries of 5 with exponential backoff
        retry = Retry(
            total=kwargs.pop("retries", 5),
            backoff_factor=kwargs.pop("backoff_factor", 0.25),
            status_forcelist=[500, 502, 503, 504],
        )
        # Configure certificate requirements for SSL connections
        cert_reqs = "CERT_NONE"
        ca_certs = None
        if not disable_cert:
            import certifi
            cert_reqs = "CERT_REQUIRED"
            ca_certs = get_environ_variable("SSL_CERT_FILE") or certifi.where()
        # Finally, create and return the PoolManager instance
        return PoolManager(
            num_pools=num_pools,
            maxsize=maxsize,
            timeout=timeout,
            retries=retry,
            cert_reqs=cert_reqs,
            ca_certs=ca_certs,
            **kwargs
        )


class MinioService(ServiceInterface[Minio]):
    instance: Minio
    metadata: dict = {}

    @classmethod
    def _create_instance(cls, disable_cert: bool = False, **kwargs) -> Minio:
        pool_configs = kwargs.pop("pool_configs", {})
        minio_configs = get_minio_from_payload(kwargs)
        if "http_client" not in minio_configs:
            logger.warning("Creating a new HTTP client for MinIO with connection pooling.")
            minio_configs["http_client"] = MinioConnectionPool.get_or_create_pool(
                disable_cert=disable_cert,
                **pool_configs
            )
        cls.metadata["minio_endpoint"] = minio_configs.get("endpoint")
        return Minio(cert_check=not disable_cert, **minio_configs)

    @classmethod
    def auto(cls, disable_cert: bool = False, **kwargs) -> "MinioService":
        cls.instance = cls._create_instance(disable_cert=disable_cert, **kwargs)
        return cls(**kwargs)

    def buckets(self) -> list[str]:
        """List all buckets in the MinIO instance."""
        return [
            bucket.name
            for bucket in self.client.list_buckets()
        ]

    def objects(self, bucket_name: str, prefix: str = "", shallow: bool = False) -> list[str]:
        """List all objects in a specific bucket in the MinIO instance."""
        return [
            obj.object_name
            for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=not shallow)
        ]

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists in the MinIO instance."""
        return self.client.bucket_exists(bucket_name)
    
    def object_info(self, bucket_name: str, object_name: str) -> dict:
        """Get metadata of an object in a specific bucket in the MinIO instance."""
        stat = self.client.stat_object(bucket_name, object_name)
        return {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "size": stat.size,
            "last_modified": stat.last_modified,
            "etag": stat.etag,
            "content_type": stat.content_type,
            "metadata": stat.metadata,
        }

    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        """Check if an object exists in a specific bucket in the MinIO instance."""
        from minio.error import S3Error

        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            logger.debug(f"Object {object_name} in bucket {bucket_name} does not exist.")
            return False

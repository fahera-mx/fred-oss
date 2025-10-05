from minio import Minio

from fred.settings import logger_manager
from fred.dao.service.interface import ServiceInterface
from fred.dao.service.utils import get_minio_from_payload
from fred.dao.service._minio.pool import MinioConnectionPool
from fred.dao.service._minio.policy.catalog import MinioPolicyCatalog

logger = logger_manager.get_logger(name=__name__)


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

    def make_bucket_public(self, bucket_name: str, readonly: bool = False):
        """Make a bucket public with either read-only or read-write access."""
        policy = MinioPolicyCatalog.BUCKET_PUBLIC_RO \
            if readonly else MinioPolicyCatalog.BUCKET_PUBLIC_RW
        self.client.set_bucket_policy(
            bucket_name=bucket_name,
            policy=policy.content(bucket_name=bucket_name)
        )

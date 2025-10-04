from dataclasses import dataclass
from typing import Iterator, Optional

from fred.settings import logger_manager, get_environ_variable
from fred.dao.service.catalog import ServiceCatalog
from fred.dao.comp.interface import ComponentInterface

logger = logger_manager.get_logger(name=__name__)


def _get_minio_elements_from_key(key: str, **kwargs) -> tuple[str, str]:
    import os

    fullpath = os.path.join(
        kwargs.pop("bucket_name", get_environ_variable("MINIO_BUCKET")) or "",
        key
    )
    bucket_name = os.path.dirname(fullpath)
    object_name = os.path.basename(fullpath)
    if not bucket_name:
        raise ValueError(
            "Bucket name must be specified either in kwargs, environment variable MINIO_BUCKET, "
            "or implicitly as part of the key."
        )
    if not object_name:
        raise ValueError("Object name cannot be empty.")
    return bucket_name, object_name


@dataclass(frozen=True, slots=True)
class FredKeyVal(ComponentInterface):
    """A simple key-value store implementation using a backend service.
    This class provides methods to interact with a key-value store, such as setting,
    getting, and deleting key-value pairs. The actual implementation of these methods
    depends on the underlying service being used (e.g., Redis).
    """
    key: str
    
    @classmethod
    def keys(cls, pattern: Optional[str] = None, **kwargs) -> Iterator[str]:
        """Returns a list of keys matching the given pattern.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the KEYS command to get the
        list of keys matching the pattern.
        Args:
            pattern (str): The pattern to match keys against. Defaults to "*".
        Returns:
            list[str]: A list of keys matching the pattern.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        match cls._cat:
            case ServiceCatalog.REDIS:
                return (
                    key if isinstance(key, str) else key.decode("utf-8")
                    for key in cls._srv.client.scan_iter(match=pattern, **kwargs)
                )
            case ServiceCatalog.STDLIB:
                import fnmatch
                pattern = pattern or "*"
                return (
                    key
                    for key in cls._srv.client._memstore_keyval.keys()
                    if fnmatch.fnmatch(key, pattern=pattern)
                )
            case ServiceCatalog.MINIO:
                import fnmatch
                pattern = pattern or "*"
                bucket_name = (
                    kwargs.get("bucket", None)
                    or kwargs.get("minio_bucket", None)
                    or get_environ_variable("MINIO_BUCKET")
                )
                if not bucket_name:
                    raise ValueError("Missing bucket info to list keys in MinIO service.")
                return (
                    key
                    for obj in cls._srv.objects(bucket_name, **kwargs)
                    if fnmatch.fnmatch((key := obj.object_name), pattern=pattern)
                )
            case _:
                raise NotImplementedError(f"Keys method not implemented for service {cls._nme}")

    def set(self, value: str, key: Optional[str] = None, **kwargs) -> None:
        """Sets a key-value pair in the store.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the SET command to store the
        key-value pair.
        Args:
            key (str): The key to set.
            value (str): The value to associate with the key.
            **kwargs: Additional keyword arguments for setting the key-value pair,
                      such as expiration time.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        key = key or self.key
        match self._cat:
            case ServiceCatalog.REDIS:
                self._srv.client.set(key, value)
                expire = kwargs.get("expire")
                if expire and isinstance(expire, int):
                    self._srv.client.expire(key, expire)
            case ServiceCatalog.STDLIB:
                self._srv.client._memstore_keyval[key] = value
                # TODO: Implement expiration logic
                if "expire" in kwargs:
                    logger.warning("Expiration not implemented for STDLIB service.")
            case ServiceCatalog.MINIO:
                # MinIO is not a key-value store, but we can simulate it:
                # the key will be the object name, and the value will be the object content.
                import io

                bucket_name, object_name = _get_minio_elements_from_key(key, **kwargs)
                # Ensure the bucket exists or create otherwise
                if not self._srv.bucket_exists(bucket_name):
                    logger.warning(f"Creating bucket since doesn't exists: {bucket_name}")
                    self._srv.client.make_bucket(bucket_name)
                if "expire" in kwargs:
                    # TODO: Implement expiration logic
                    logger.warning("Expiration not implemented for MINIO service.")
                # Prepare the value as a byte stream
                value_bytes = value.encode("utf-8")
                if kwargs.get("b64", False):
                    import base64
                    value_bytes = base64.b64decode(value)
                value_stream = io.BytesIO(value_bytes)
                value_stream.seek(0)  # Ensure the stream is at the beginning
                # Put the object into the bucket
                self._srv.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=value_stream,
                    length=len(value_bytes),
                )
            case _:
                raise NotImplementedError(f"Set method not implemented for service {self._nme}")

    def get(self, key: Optional[str] = None, fail: bool = False) -> Optional[str]:
        """Gets the value associated with a key from the store.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the GET command to retrieve the
        value associated with the key.
        Args:
            key (str): The key to retrieve.
            fail (bool): If True, raises a KeyError if the key is not found. Defaults to False.
        Returns:
            Optional[str]: The value associated with the key, or None if the key is not found
                           and fail is False.
        Raises:
            KeyError: If the key is not found and fail is True.
            NotImplementedError: If the method is not implemented for the current service.
        """
        key = key or self.key
        result = None
        match self._cat:
            case ServiceCatalog.REDIS:
                result = self._srv.client.get(key)
            case ServiceCatalog.STDLIB:
                result = self._srv.client._memstore_keyval.get(key)
            case ServiceCatalog.MINIO:
                bucket_name, object_name = _get_minio_elements_from_key(key)
                # Verify if the bucket exists
                if not self._srv.bucket_exists(bucket_name):
                    logger.warning(f"Bucket {bucket_name} does not exist.")
                    if fail:
                        raise KeyError(f"Bucket {bucket_name} does not exist.")
                    return None
                # Verify if the object exists
                if not self._srv.object_exists(bucket_name, object_name):
                    logger.warning(f"Object {object_name} in bucket {bucket_name} does not exist.")
                    if fail:
                        raise KeyError(f"Object {object_name} not found in bucket {bucket_name}.")
                    return None
                try:
                    response = self._srv.client.get_object(bucket_name, object_name)
                    result_bytes = response.read()
                    result = result_bytes.decode("utf-8")
                except Exception as e:
                    logger.error(f"Error retrieving object {object_name} from bucket {bucket_name}: {e}")
                    result = None
                    if fail:
                        raise KeyError(f"Object {object_name} not found in bucket {bucket_name}.")
                finally:
                    response.close()
                    response.release_conn()
            case _:
                raise NotImplementedError(f"Get method not implemented for service {self._nme}")
        if fail and result is None:
            raise KeyError(f"Key {key} not found.")
        return result

    def delete(self, key: Optional[str] = None) -> None:
        """Deletes a key-value pair from the store.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the DEL command to remove the
        key-value pair.
        Args:
            key (str): The key to delete.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        key = key or self.key
        match self._cat:
            case ServiceCatalog.REDIS:
                self._srv.client.delete(key)
            case ServiceCatalog.STDLIB:
                self._srv.client._memstore_keyval.pop(key, None)
            case ServiceCatalog.MINIO:
                bucket_name, object_name = _get_minio_elements_from_key(key)
                # Verify if the bucket exists
                if not self._srv.bucket_exists(bucket_name):
                    logger.warning(f"Bucket {bucket_name} does not exist.")
                    return
                # Verify if the object exists
                if not self._srv.object_exists(bucket_name, object_name):
                    logger.warning(f"Object {object_name} in bucket {bucket_name} does not exist.")
                    return
                try:
                    self._srv.client.remove_object(bucket_name, object_name)
                except Exception as e:
                    logger.error(f"Error deleting object {object_name} from bucket {bucket_name}: {e}")
            case _:
                raise NotImplementedError(f"Delete method not implemented for service {self._nme}")

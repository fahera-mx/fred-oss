from dataclasses import dataclass
from typing import Optional

from fred.dao.service.catalog import ServiceCatalog
from fred.dao.comp.interface import ComponentInterface


@dataclass(frozen=True, slots=True)
class FredKeyVal(ComponentInterface):
    """A simple key-value store implementation using a backend service.
    This class provides methods to interact with a key-value store, such as setting,
    getting, and deleting key-value pairs. The actual implementation of these methods
    depends on the underlying service being used (e.g., Redis).
    """
    
    def set(self, key: str, value: str, **kwargs) -> None:
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
        match self._cat:
            case ServiceCatalog.REDIS:
                self._srv.client.set(key, value)
                expire = kwargs.get("expire")
                if expire and isinstance(expire, int):
                    self._srv.client.expire(key, expire)
            case _:
                raise NotImplementedError(f"Set method not implemented for service {self._nme}")

    def get(self, key: str, fail: bool = False) -> Optional[str]:
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
        match self._cat:
            case ServiceCatalog.REDIS:
                result = self._srv.client.get(key)
                if result is None and fail:
                    raise KeyError(f"Key {key} not found.")
                return result
            case _:
                raise NotImplementedError(f"Get method not implemented for service {self._nme}")

    def delete(self, key: str) -> None:
        """Deletes a key-value pair from the store.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the DEL command to remove the
        key-value pair.
        Args:
            key (str): The key to delete.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        match self._cat:
            case ServiceCatalog.REDIS:
                self._srv.client.delete(key)
            case _:
                raise NotImplementedError(f"Delete method not implemented for service {self._nme}")
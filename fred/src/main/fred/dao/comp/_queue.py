from dataclasses import dataclass
from typing import Optional

from fred.dao.service.catalog import ServiceCatalog
from fred.dao.comp.interface import ComponentInterface


@dataclass(frozen=True, slots=True)
class FredQueue(ComponentInterface):
    """A simple queue implementation using a backend service.
    This class provides methods to interact with a queue, such as adding,
    removing, and checking the size of the queue. The actual implementation
    of these methods depends on the underlying service being used (e.g., Redis).
    Attributes:
        name: str: The name of the queue.
    """
    name: str

    def size(self) -> int:
        """Returns the number of items in the queue.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the LLEN command to get the
        length of the list representing the queue.
        Returns:
            int: The number of items in the queue.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        match self._cat:
            case ServiceCatalog.REDIS:
                return self._srv.client.llen(self.name)
            case _:
                raise NotImplementedError(f"Size method not implemented for service {self._nme}")

    def clear(self) -> None:
        """Clears all items from the queue.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the DEL command to remove the
        key representing the queue.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        match self._cat:
            case ServiceCatalog.REDIS:
                self._srv.client.delete(self.name)
            case _:
                raise NotImplementedError(f"Clear method not implemented for service {self._nme}")

    def add(self, item: str) -> None:
        """Adds an item to the queue.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the LPUSH command to add the
        item to the front of the list representing the queue.
        Args:
            item (str): The item to add to the queue.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        match self._cat:
            case ServiceCatalog.REDIS:
                self._srv.client.lpush(self.name, item)
            case _:
                raise NotImplementedError(f"Add method not implemented for service {self._srv._nme}")

    def pop(self) -> Optional[str]:
        """Removes and returns an item from the queue.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the RPOP command to remove and
        return the last item from the list representing the queue.
        Returns:
            Optional[str]: The item removed from the queue, or None if the queue is empty.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        match self._cat:
            case ServiceCatalog.REDIS:
                return self._srv.client.rpop(self.name)
            case _:
                raise NotImplementedError(f"Pop method not implemented for service {self._srv._nme}")

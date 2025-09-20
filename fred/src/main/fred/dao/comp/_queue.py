from dataclasses import dataclass
from typing import Optional

from fred.settings import logger_manager
from fred.dao.service.catalog import ServiceCatalog
from fred.dao.comp.interface import ComponentInterface

logger = logger_manager.get_logger(name=__name__)


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
            case ServiceCatalog.STDLIB:
                q = self._srv.client._memstore_queue.get(self.name, None)
                return q.qsize() if q else 0
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
            case ServiceCatalog.STDLIB:
                if (q := self._srv.client._memstore_queue.pop(self.name, None)):
                    del q
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
            case ServiceCatalog.STDLIB:
                from queue import Queue
                qs = self._srv.client._memstore_queue
                q = qs[self.name] = qs.get(self.name, None) or Queue()
                q.put(item)
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
            case ServiceCatalog.STDLIB:
                from queue import Empty
                if not (q := self._srv.client._memstore_queue.get(self.name, None)):
                    return None
                try:
                    return q.get_nowait()
                except Empty:
                    logger.info(f"Queue '{self.name}' is empty.")
                    return None
            case _:
                raise NotImplementedError(f"Pop method not implemented for service {self._srv._nme}")

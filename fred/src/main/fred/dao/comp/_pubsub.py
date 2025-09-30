import uuid
from dataclasses import dataclass
from typing import Optional

from fred.settings import logger_manager
from fred.dao.service.catalog import ServiceCatalog
from fred.dao.comp.interface import ComponentInterface

logger = logger_manager.get_logger(name=__name__)


class FredSubscriptionMixin:
    # TODO: Improve typing... and better underlying subscriptions management!
    # This only works within the same python process.
    subs: dict = {}


@dataclass(frozen=True, slots=True)
class FredPubSub(ComponentInterface, FredSubscriptionMixin):
    """A simple publish-subscribe (pub-sub) implementation using a backend service.
    This class provides methods to interact with pub-sub channels, such as publishing
    messages, subscribing to channels, and managing subscriptions. The actual implementation
    of these methods depends on the underlying service being used (e.g., Redis).
    Attributes:
        name: str: The name of the pub-sub channel.
    """
    name: str

    def publish(self, item: str) -> int:
        match self._cat:
            case ServiceCatalog.REDIS:
                return self._srv.client.publish(self.name, item)
            case ServiceCatalog.STDLIB:
                raise NotImplementedError("Publish method not implemented for STDLIB service")
            case _:
                raise NotImplementedError(f"Publish method not implemented for service {self._nme}")

    def subscribe(self, subscription_id: Optional[str] = None):
        """Clears all items from the queue.
        The implementation of this method depends on the underlying service.
        For example, if the service is Redis, it uses the DEL command to remove the
        key representing the queue.
        Raises:
            NotImplementedError: If the method is not implemented for the current service.
        """
        subscription_id = subscription_id or (
            logger.info(f"Creating new subscriber for channel: {self.name}")
            or str(uuid.uuid4())
        )
        logger.info(f"Using subscription ID: {subscription_id}")
        match self._cat:
            case ServiceCatalog.REDIS:
                subscriber = self.subs[subscription_id] = self.subs.get(subscription_id, None) or self._srv.client.pubsub()
                subscriber.subscribe(self.name)
                yield from subscriber.listen()
            case ServiceCatalog.STDLIB:
                raise NotImplementedError("Subscribe method not implemented for STDLIB service")
            case _:
                raise NotImplementedError(f"Clear method not implemented for service {self._nme}")

    @classmethod
    def unsubscribe(cls, subscription_id: str) -> None:
        logger.warning(
            "Consider that the current implementation only allows unsubscribing "
            "within the same underlying python process."
        )
        # Early exit if subscription_id does not exist
        if subscription_id not in cls.subs:
            logger.warning(f"No active subscription found for ID: {subscription_id}")
            return
        # Pop-out the subscriber from the shared subscriptions dictionary
        subscriber = cls.subs.pop(subscription_id)
        match cls._cat:
            case ServiceCatalog.REDIS:
                subscriber.unsubscribe()
                subscriber.close()
            case ServiceCatalog.STDLIB:
                raise NotImplementedError("Unsubscribe method not implemented for STDLIB service")
            case _:
                raise NotImplementedError(f"Unsubscribe method not implemented for service {cls._nme}")

    @classmethod
    def subscribers(cls) -> list[str]:
        return list(cls.subs.keys())

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
        """Subscribe to the pub/sub channel and yield messages as they arrive.

        This method creates (or reuses) a subscription to the channel specified by `self.name`.
        It returns a generator that yields messages received on the channel.
        The implementation depends on the underlying service (e.g., Redis).

        Args:
            subscription_id (Optional[str]): An optional identifier for the subscription. If not provided, a new UUID is generated.

        Yields:
            Messages received from the channel.
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
                raise NotImplementedError(f"Subscribe method not implemented for service {self._nme}")

    @classmethod
    def unsubscribe(cls, subscription_id: str, close: bool = False) -> None:
        # TODO: Implement the 'unsubscribe' and optially close the subscriber.
        logger.error("The unsubscribe method not implemented yet.")
        raise NotImplementedError("Unsubscribe method not implemented yet.")

    @classmethod
    def subscribers(cls) -> list[str]:
        # TODO: Implement the 'subscribers' method to list active subscriptions.
        logger.error("The subscribers method not implemented yet.")
        raise NotImplementedError("Subscribers method not implemented yet.")

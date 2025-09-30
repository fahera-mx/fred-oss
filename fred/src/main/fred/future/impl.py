import time
from threading import Thread
from typing import (
    Callable,
    Optional,
    TypeVar,
)

from fred.settings import logger_manager
from fred.future.settings import FRD_FUTURE_DEFAULT_EXPIRATION
from fred.future.callback.interface import CallbackInterface
from fred.monad.interface import MonadInterface
from fred.monad.catalog import EitherMonad
from fred.future.result import (
    FutureResult,
    FutureUndefinedPending,
    FutureUndefinedInProgress,
    FutureDefined,
)

A = TypeVar("A")
B = TypeVar("B")

logger = logger_manager.get_logger(__name__)


class Future(MonadInterface[A]):
    """A Future represents a computation that will complete at some point in the future,
    yielding a result of type A or failing with an exception. It allows for asynchronous
    programming by enabling non-blocking operations and chaining of computations.
    This implementation uses threading to execute the computation in a separate thread.

    The Future class provides methods to wait for the computation to complete,
    retrieve the result, and chain further computations using flat_map and map.

    Note: This implementation is a simplified version and may not cover all edge cases
    or provide advanced features found in more comprehensive concurrency libraries.

    Note: The Future class is designed to work with the Either monad to encapsulate
    successful results (Right) and exceptions (Left).

    Note: The Future class uses a backend storage system to persist the state
    and result of the computation, allowing for distributed or long-running tasks.

    Note: The Future class is generic and can be used with any type A, allowing for
    flexibility in the types of computations it can represent.

    Note: Even though the Future class implements the MonadInterface, it is not a full monad
    in the traditional sense, as it represents an asynchronous computation rather than
    a pure value. However, it provides similar capabilities for chaining and transforming
    computations in a functional style.

    TODO: Consider adding cancellation support to allow aborting ongoing computations.
    
    TODO: Analyze impact on performance and resource usage when using many Futures. Specially
    on garbage collection and memory leaks.
    
    TODO: Consider using more advanced concurrency primitives for better control and efficiency.
    """

    def __init__(
            self,
            function: Callable[..., A],
            on_start: Optional[CallbackInterface] = None,
            on_complete: Optional[CallbackInterface] = None,
            parent_id: Optional[str] = None,
            broadcast: bool = False,
            **kwargs
        ):
        """Initializes a Future with the provided function to be executed asynchronously.
        The function is executed in a separate thread, allowing for non-blocking operations.

        Args:
            function (Callable[..., A]): The function to be executed asynchronously.
            future_id (Optional[str], keyword-only): A reserved keyword-only parameter used to
                uniquely identify this Future instance. This value is consumed by the Future
                infrastructure and is not passed to the target function.
            **kwargs: Additional keyword arguments to be passed to the function when executed.
                All keyword arguments except 'future_id' are forwarded to the target function.
        """
        # Create a new available future
        future = FutureUndefinedPending.auto(
            parent_id=parent_id,
            broadcast=broadcast,
            future_id=kwargs.pop("future_id", None),
        )
        # Register the Future-ID and define the available future via the provided function.
        # Note: The 'apply' method is blocking by itself; thus, we run it in a separate thread.
        # Note: The thread is a daemon to ensure it does not block program exit.
        self.future_id = future.future_id
        self.parent_id = parent_id
        self.thread = Thread(
            target=lambda: future.apply(
                function=function,
                on_complete=on_complete,
                on_start=on_start,
                **kwargs
            ),
            daemon=True,
        )
        # Start the thread to execute the function asynchronously
        self.thread.start()

    @property
    def _result(self) -> Optional[FutureResult[A]]:
        return FutureResult.from_backend(future_id=self.future_id)
    
    @property
    def _status(self) -> Optional[str]:
        return FutureResult._get_status_key(future_id=self.future_id).get()

    @property
    def _output(self) -> Optional[str]:
        return FutureResult._get_output_key(future_id=self.future_id).get()

    def wait(self, timeout: Optional[float] = None) -> EitherMonad.Either[A]:
        """Waits for the future to complete and returns the result as an Either monad.

        TL;DR Waiting will collapse the future into a concrete result
        which can be either a value (Right) or an exception (Left).

        * If the future completes successfully, returns Right(value).
        * If the future fails, returns Left(exception).
        * If the timeout is reached before completion, raises a TimeoutError.
        Args:
            timeout (Optional[float]): Maximum time to wait for the future to complete.
                                       If None, waits indefinitely.
        Returns:
            Either[A]: An Either monad containing the result or exception.
        Raises:
            TimeoutError: If the future does not complete within the specified timeout.
            RuntimeError: If the future status is inconsistent after waiting.
            TypeError: If the future result type is unknown.
        """
        # Wait for the thread to complete or timeout
        self.thread.join(timeout=timeout)
        if self.thread.is_alive():
            raise TimeoutError("Future did not complete within the specified timeout.")
        # After the thread has completed, check the status consistency
        if not self._status:
            raise RuntimeError("Future status should be set but isn't.")
        if not self._status.startswith("DEFINED"):
            raise RuntimeError("Future status should be DEFINED after wait.")
        # Check the result-type consistency
        # If the future is still pending or in-progress, it's an error and should not happen
        # If the future is defined, return the contained value or exception
        match self._result:
            case FutureUndefinedPending():
                raise RuntimeError("Future is still pending after wait.")
            case FutureUndefinedInProgress():
                raise RuntimeError("Future is still in progress after wait.")
            case FutureDefined(value=value):
                return value
            case _:
                raise TypeError("Unknown FutureResult type")

    def getwhatevernow(self) -> Optional[EitherMonad.Either[A]]:
        """Gets the current result of the future without waiting.
        If the future is not yet completed, returns None.
        If the future is completed, returns the result as an Either monad.

        Returns:
            Optional[Either[A]]: None if the future is not completed; otherwise, an Either monad containing the result or exception.
        """
        match self._result:
            case FutureDefined(value=value):
                return value
            case _:
                return None

    @property
    def state(self) -> Optional[str]:
        """Returns the current state of the future as a string.
        The state is derived from the status key in the backend storage.
        Returns:
            Optional[str]: The current state of the future, or None if not available.
                           Possible states include:
                           - "UNDEFINED:PENDING"
                           - "UNDEFINED:IN_PROGRESS"
                           - "DEFINED:SUCCESS"
                           - "DEFINED:FAILURE"
        """
        return ":".join(self._status.split(":")[:2]) if self._status else None

    def __repr__(self) -> str:
        return f"FUTURE[{self.state}]('{self.future_id}')"
    
    def __str__(self) -> str:
        return self.future_id

    def wait_and_resolve(self, timeout: Optional[float] = None) -> A:
        """Waits for the future to complete and resolves the result into
        the expected output type of the function call; raises if the future failed.
        This is a convenience method that combines waiting for the future to complete
        and resolving the result, raising any exceptions that occurred during execution.
        Args:
            timeout (Optional[float]): Maximum time to wait for the future to complete.
                                       If None, waits indefinitely.
        Returns:
            A: The resolved value of the future if it completed successfully.
        Raises:
            TimeoutError: If the future does not complete within the specified timeout.
            Exception: If the future failed during execution, the original exception is raised.
        """
        return self.wait(timeout=timeout).resolve()

    @classmethod
    def from_value(cls, val: A, **kwargs) -> 'Future[A]':
        """
        Creates a Future that is immediately resolved with the given value.

        Args:
            val (A): The value to resolve the Future with.
            **kwargs: Additional keyword arguments forwarded to the Future constructor.
                These may include parameters such as:
                    - parent_id (Optional[str]): The parent future's ID.
                    - expiration (Optional[float]): Expiration time for the future.
                    - callback (Optional[CallbackInterface]): Callback to invoke on completion.
                For a full list of accepted parameters, see the Future class documentation.
        Returns:
            Future[A]: A Future instance resolved with the provided value.
        """
        return Future(function=lambda: val, **kwargs)
    
    def flat_map(self, function: Callable[[A], 'Future[B]'], timeout: Optional[float] = None) -> 'Future[B]':
        """Chains the current future with another future-producing function.
        This method allows for sequential asynchronous operations where the output
        of one future is used as the input to another.

        The simple implementation of this method is: function(self.wait_and_resolve())
        Nonetheless, the simple implementation would block the current thread
        until the first future is resolved, which is not ideal in an asynchronous context.
        Instead, we create a new Future that encapsulates the entire operation,
        allowing it to be executed asynchronously.

        Args:
            function (Callable[[A], Future[B]]): A function that takes the result of the
                                                  current future and returns a new Future.
            timeout (Optional[float]): Maximum time to wait for the current future to complete.
                                       If None, waits indefinitely.
        Returns:
            Future[B]: A new Future representing the chained operation."""
        # TODO: Is there a more efficient implementation?
        return Future(
            parent_id=self.future_id,
            function=lambda:
                function(self.wait_and_resolve(timeout=timeout))
                .wait_and_resolve(timeout=timeout)
        )

    def map(self, function: Callable[[A], B]) -> 'Future[B]':
        """Applies a function to the result of the future, returning a new future.
        This method allows for transforming the result of a future without blocking.

        Original implementation:
        return self.flat_map(function=lambda value: type(self).from_value(function(value)))

        However, that implementation would create an intermediate Future just to
        hold the transformed value, which is unnecessary overhead. Instead, we can directly create a new Future
        that applies the transformation function to the result of the current future.

        Args:
            function (Callable[[A], B]): A function that takes the result of the current future
                                          and returns a new value.
        Returns: Future[B]: A new Future containing the transformed result.
        """
        return Future(
            function=lambda: function(self.wait_and_resolve()),
            parent_id=self.future_id,
        )

    @classmethod
    def pullsync(
            cls,
            future_id: str,
            retry_delay: float = 0.2,
            retry_backoff_rate: float = 0.1,
            retry_delay_max: float = 15,
            timeout: float = FRD_FUTURE_DEFAULT_EXPIRATION,
            on_complete: Optional[CallbackInterface] = None,
            **kwargs
        ) -> 'Future[A]':
        """Pulls an existing future from the backend storage by its ID.
        This method allows for retrieving and interacting with a future
        that was previously created and stored in the backend.

        Args:
            future_id (str): The unique identifier of the future to be pulled.
            retry_delay (float): Initial delay between checks for the future's completion.
            retry_backoff_rate (float): Incremental increase in delay after each check.
            retry_delay_max (float): Maximum delay between checks.
            timeout (float): Maximum time to wait for the future to complete.
            on_complete (Optional[CallbackInterface]): An optional callback to be executed
                                                      when the future completes.
            **kwargs: Additional keyword arguments to be passed to the Future constructor.
        Returns:
            Future[A]: A Future instance representing the pulled future.
        """
        logger.warning(
            "The 'pullsync' method is scheduled for deprecation and will be removed in future versions. "
            "Please use the 'subscribe' method instead that uses a pubsub mechanism."
        )
        from fred.future.utils import pull_future_result

        return cls(
            function=lambda: pull_future_result(
                future_id=future_id,
                retry_delay=retry_delay,
                retry_backoff_rate=retry_backoff_rate,
                retry_delay_max=retry_delay_max,
                timeout=timeout,
            ),
            on_complete=on_complete,
            **kwargs
        )

    @classmethod
    def subscribe(
            cls,
            future_id: str,
            on_start: Optional[CallbackInterface] = None,
            on_complete: Optional[CallbackInterface] = None,
            retry_delay: float = 0.2,
            retry: int = 3,
    ) -> 'Future[A]':
        """Subscribes to updates for an existing future using a publish-subscribe mechanism.
        This method allows for receiving real-time updates about the future's state
        and result without blocking.
        Args:
            future_id (str): The unique identifier of the future to subscribe to.
            on_start (Optional[CallbackInterface]): An optional callback to be executed
                                                   when the subscription starts.
            on_complete (Optional[CallbackInterface]): An optional callback to be executed
                                                      when the future completes.
        Returns:
            Future[A]: A Future instance that will execute the subscription logic.
        """
        # TODO: Consider adding a timeout parameter to avoid waiting indefinitely...
        # TODO: There's a known issue where if the future completes before we subscribe,
        #       we might miss the completion message.
        # Define a closure that will handle incoming messages from the pub-sub channel
        def closure():
            for payload in FutureResult._get_bcast_channel(future_id=future_id).subscribe():
                logger.info(f"Received pubsub message for future '{future_id}': {payload}")
                if payload.get("type") != "message":
                    continue
                message = payload.get("data")
                if not message:
                    continue
                match FutureResult.from_string(message):
                    case FutureDefined(value=value):
                        return value.resolve()
                    case FutureUndefinedPending():
                        continue
                    case FutureUndefinedInProgress():
                        continue
                    case _:
                        raise TypeError("Unknown FutureResult type")
        shared_params = {
            "parent_id": future_id,
            "broadcast": False,
            "on_start": on_start,
            "on_complete": on_complete,
        }
        # Depending on the current state of the future, either return the resolved value
        # or subscribe to the broadcast channel to wait for updates (via closure).
        match FutureResult.from_backend(future_id=future_id):
            case FutureDefined(value=value):
                return cls(
                    function=lambda: value.resolve(),
                    **shared_params
                )
            case instance:
                # The future-result can be None if the future_id does not exist
                if not instance:
                    if retry <= 0:
                        raise ValueError(f"Future with ID '{future_id}' does not exist.")
                    logger.error(f"Future with ID '{future_id}' does not exist; attempting to retry ({retry} retries left).")
                    time.sleep(retry_delay)
                    return cls.subscribe(
                        future_id=future_id,
                        on_start=on_start,
                        on_complete=on_complete,
                        retry_delay=retry_delay,
                        retry=max(0, retry - 1),
                    )
                # If the future exists, but is not configured for broadcast, raise an error...
                if not instance.broadcast:
                    raise ValueError("Future is not configured for broadcast; cannot subscribe.")
                # If the future exists and is configured for broadcast, subscribe to updates...
                logger.info(f"Subscribing to future '{future_id}' via broadcast channel.")
                return cls(
                    function=closure,
                    **shared_params
                )

    def lineage(self) -> list[str]:
        """Retrieves the lineage of the future, tracing back through its parent futures.
        This method is useful for debugging and understanding the sequence of computations
        that led to the current future.
        Returns:
            list[str]: A list of future IDs representing the lineage, starting from the current future
                       and tracing back through its parents.
        """
        logger.warning(
            "The 'lineage' method should only be used for debugging purposes "
            "as it may have performance implications and unreliable lineage due to "
            "possible missing parent_id values caused by cleanup or TTL expiration."
        )
        if not (fr := FutureResult.from_backend(future_id=self.future_id)):
            logger.error(f"Current future_id '{self.future_id}' does not exist in backend.")
            return []
        return fr._lineage()

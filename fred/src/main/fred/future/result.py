import json
from time import perf_counter
from dataclasses import dataclass
from typing import (
    Callable,
    Generic,
    Optional,
    TypeVar,
)

from fred.settings import (
    get_environ_variable,
    logger_manager,
)
from fred.future.settings import (
    FRD_FUTURE_BACKEND,
    FRD_FUTURE_DEFAULT_EXPIRATION,
    FRD_FUTURE_DEFAULT_TIMEOUT,
)
from fred.future.callback.interface import CallbackInterface
from fred.dao.service.catalog import ServiceCatalog
from fred.utils.dateops import datetime_utcnow
from fred.dao.comp.catalog import FredKeyVal, FredQueue, FredPubSub
from fred.monad.catalog import EitherMonad

logger = logger_manager.get_logger(__name__)

A = TypeVar("A")


class FutureBackend:
    keyval: type[FredKeyVal]
    queue: type[FredQueue]
    pubsub: type[FredPubSub]

    @classmethod
    def with_backend(cls, service: ServiceCatalog, **kwargs) -> type['FutureBackend']:
        """Dynamically creates a FutureBackend subclass with the specified service backend.
        This method uses the service catalog to fetch the appropriate components for the
        given service and constructs a new subclass of FutureBackend with those components.
        Args:
            service (ServiceCatalog): The service catalog entry representing the backend service.
            **kwargs: Additional keyword arguments to pass to the component catalog.
        Returns:
            type[FutureBackend]: A new subclass of FutureBackend configured with the specified backend.
        """
        components = service.component_catalog(**kwargs)
        return type(
            f"{service.name.title()}{cls.__name__}",
            (cls,),
            {
                "keyval": components.KEYVAL.value,
                "queue": components.QUEUE.value,
                "pubsub": components.PUBSUB.value,
            },
        )

    @classmethod
    def infer_backend(cls, env: Optional[str] = None, **kwargs) -> type['FutureBackend']:
        """Infers the backend service from the environment variable or defaults to FRD_FUTURE_BACKEND.
        This method checks for an environment variable to determine the backend service. If the
        environment variable is not set, it defaults to the value of FRD_FUTURE_BACKEND. It then
        uses the inferred service to create a FutureBackend subclass with the appropriate components.
        Args:
            env (Optional[str]): The name of the environment variable to check for the backend service.
                                 If None, defaults to FRD_FUTURE_BACKEND.
            **kwargs: Additional keyword arguments to pass to the component catalog.
        Returns:
            type[FutureBackend]: A new subclass of FutureBackend configured with the inferred backend.
        """
        service_key = get_environ_variable(env, default=ServiceCatalog.STDLIB.name) \
            if env else FRD_FUTURE_BACKEND
        return cls.with_backend(
            service=ServiceCatalog[service_key.upper()],
            **kwargs
        )


@dataclass(frozen=True, slots=False)
class FutureResult(Generic[A], FutureBackend.infer_backend()):
    """Represents the result of an asynchronous computation (Future).
    This class provides methods to manage and retrieve the status and output of a Future.
    It uses a key-value store to persist the state and result of the Future, allowing for
    retrieval and management of asynchronous tasks."""
    future_id: str
    parent_id: Optional[str]
    broadcast: bool

    @staticmethod
    def _get_future_keyname(future_id: str) -> str:
        return ":".join(["frd", "future", future_id])

    @property
    def future_keyname(self) -> str:
        return self._get_future_keyname(future_id=self.future_id)
    
    @classmethod
    def _get_bcast_channel(cls, future_id: str) -> FredPubSub:
        return cls.pubsub(name=":".join([cls._get_future_keyname(future_id=future_id), "bcast"]))

    @property
    def bcast_channel(self) -> FredPubSub:
        return self._get_bcast_channel(future_id=self.future_id)

    def bcast_now(self, item: Optional[str] = None, ignore_flag: bool = False) -> bool:
        if ignore_flag or self.broadcast:
            self.bcast_channel.publish(item=item or self.stringify())
            return True
        return False

    @classmethod
    def _get_status_key(cls, future_id: str) -> FredKeyVal:
        return cls.keyval(key=":".join([cls._get_future_keyname(future_id=future_id), "status"]))

    @property
    def status(self) -> FredKeyVal:
        return self._get_status_key(future_id=self.future_id)
    
    @classmethod
    def _get_output_key(cls, future_id: str) -> FredKeyVal:
        return cls.keyval(key=":".join([cls._get_future_keyname(future_id=future_id), "output"]))

    @property
    def output(self) -> FredKeyVal:
        return self._get_output_key(future_id=self.future_id)
    
    @classmethod
    def _get_obj_key(cls, future_id: str) -> FredKeyVal:
        return cls.keyval(key=":".join([cls._get_future_keyname(future_id=future_id), "obj"]))

    @property
    def obj(self) -> FredKeyVal:
        return self._get_obj_key(future_id=self.future_id)

    def stringify(self) -> str:
        import pickle
        import base64
        return base64.b64encode(pickle.dumps(self)).decode("ascii")

    @classmethod
    def from_string(cls, payload: str) -> 'FutureResult[A]':
        import pickle
        import base64
        return pickle.loads(base64.b64decode(payload))
    
    def _from_backend(self) -> Optional['FutureResult[A]']:
        payload = self.obj.get()
        if not payload:
            return
        return self.from_string(payload=payload)

    @classmethod
    def from_backend(cls, future_id: str) -> Optional['FutureResult[A]']:
        return FutureResult(future_id=future_id, parent_id=None, broadcast=False)._from_backend()

    @property
    def _pre(self) -> Optional['FutureResult']:
        if not self.parent_id:
            return None
        return FutureResult.from_backend(future_id=self.parent_id)

    def _lineage(self) -> list[str]:
        if not self.parent_id:
            return [self.future_id]
        if not (parent := self._pre):
            logger.warning(
                f"Cannot retrieve full lineage for Future[{self.future_id}] "
                f"due to missing parent_id '{self.parent_id}'"
            )
            return [self.future_id, self.parent_id]
        return [self.future_id, *parent._lineage()]


@dataclass(frozen=True, slots=False)
class FutureUndefinedPending(FutureResult[A]):

    @classmethod
    def auto(cls, **kwargs) -> 'FutureUndefinedPending[A]':
        """Creates a FutureUndefinedPending instance with an auto-generated future_id.
        This method generates a unique identifier for the future_id if one is not provided
        in the keyword arguments. It ensures that each instance has a distinct future_id,
        which is essential for tracking and managing asynchronous tasks.
        Args:
            **kwargs: Additional keyword arguments to pass to the FutureUndefinedPending constructor.
        Returns:
            FutureUndefinedPending[A]: A new instance of FutureUndefinedPending with a unique future_id.
        """
        import uuid
        parent_id = kwargs.pop("parent_id", None)
        future_id = kwargs.pop("future_id", None) or str(uuid.uuid4())
        broadcast = kwargs.pop("broadcast", False)
        return FutureUndefinedPending[A](future_id=future_id, parent_id=parent_id, broadcast=broadcast, **kwargs)

    def __post_init__(self):
        logger.debug(f"Future[{self.future_id}] initialized and pending execution")
        self.status.set(
            value=f"UNDEFINED:PENDING:{datetime_utcnow().isoformat()}",
            expire=FRD_FUTURE_DEFAULT_EXPIRATION
        )
        self.obj.set(
            value=(obj_payload := self.stringify()),
            expire=FRD_FUTURE_DEFAULT_EXPIRATION
        )
        self.bcast_now(item=obj_payload, ignore_flag=False)

    def apply(
            self,
            function: Callable[..., A],
            on_start: Optional[CallbackInterface] = None,
            on_complete: Optional[CallbackInterface] = None,
            **kwargs
        ) -> 'FutureDefined[A]':
        """Applies a function to the Future, transitioning it from pending to in-progress and finalizing as defined.
        This method executes the provided function with the given keyword arguments,
        transitioning the Future from a pending state to an in-progress state. It captures
        the result of the function execution, which can be either a successful value or an
        exception, and returns a FutureDefined instance representing the completed state.
        Args:
            function (Callable[..., A]): The function to execute, which should return a value of type A.
            **kwargs: Additional keyword arguments to pass to the function during execution.
        Returns:
            FutureDefined[A]: A new instance of FutureDefined representing the completed state of the Future.
        """
        fip = FutureUndefinedInProgress[A](
            future_id=self.future_id,
            parent_id=self.parent_id,
            broadcast=self.broadcast,
            started_at=perf_counter(),
            function_name=function.__name__,
        )
        return fip.exec(
            function=function,
            on_start=on_start,
            on_complete=on_complete,
            **kwargs
        )


@dataclass(frozen=True, slots=False)
class FutureUndefinedInProgress(FutureResult[A]):
    started_at: float
    function_name: str
    

    def __post_init__(self):
        logger.debug(f"Future[{self.future_id}] started execution of function '{self.function_name}'")
        self.status.set(
            value=f"UNDEFINED:IN_PROGRESS:{datetime_utcnow().isoformat()}",
            expire=FRD_FUTURE_DEFAULT_EXPIRATION
        )
        self.obj.set(
            value=(obj_payload := self.stringify()),
            expire=FRD_FUTURE_DEFAULT_EXPIRATION
        )
        self.bcast_now(item=obj_payload, ignore_flag=False)

    def exec(
            self,
            function: Callable[..., A],
            on_start: Optional[CallbackInterface] = None,
            on_complete: Optional[CallbackInterface] = None,
            fail: bool = False,
            **kwargs,
        ) -> 'FutureDefined[A]':
        """Executes the function associated with the Future, capturing its result or exception.
        This method runs the provided function with the given keyword arguments, capturing
        its output. If the function executes successfully, it wraps the result in a Right
        monad; if it raises an exception, it captures the exception in a Left monad.
        The method returns a FutureDefined instance containing the result of the execution.
        If the 'fail' parameter is set to True, any exception raised during function execution
        will be propagated instead of being captured in the Left monad.
        Args:
            function (Callable[..., A]): The function to execute, which should return a value of type A.
            fail (bool): If True, exceptions raised during function execution will be propagated. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the function during execution.
        Returns:
            FutureDefined[A]: A new instance of FutureDefined representing the completed state of the Future.
        """
        # Execute on_start callback if provided
        on_start_thread = (
            logger.debug(f"Future[{self.future_id}] executing on_start callback")
            or on_start.run(future_id=self.future_id, blocking=False)
        ) if on_start else None
        try:
            ok = False
            match function(**kwargs):
                case EitherMonad.Right(value=value):
                    ok = True
                    value =EitherMonad.Right.from_value(val=value)
                case EitherMonad.Left(exception=exception):
                    ok = False
                    value = EitherMonad.Left.from_value(val=exception)
                case value:
                    ok = True
                    value = EitherMonad.Right.from_value(val=value)      
        except Exception as e:
            ok = False
            value = EitherMonad.Left.from_value(val=e)
            if fail:
                raise e
        future_defined = FutureDefined(
            future_id=self.future_id,
            parent_id=self.parent_id,
            broadcast=self.broadcast,
            value=value,
            ok=ok,
        )
        # We could do the following to have an "on_success" behaviour:
        # value.map(lambda v: on_complete.run(v) if on_complete else None)
        # But that would leave out the "on_failure" behaviour and we would probably need to
        # add specific 'on_success' and 'on_failure' callbacks to mitigate that.
        # Instead, we just do a generic 'on_complete' callback that gets executed
        # wrapped on an Either monad so the user can handle success/failure as needed.
        if on_complete:
            logger.debug(f"Future[{self.future_id}] executing on_complete callback")
            on_complete.run(future_id=self.future_id, output=value, blocking=True)
        if on_start_thread:
            on_start_thread.join()
        return future_defined


@dataclass(frozen=True, slots=False)
class FutureDefined(FutureResult[A]):
    value: EitherMonad.Either[A]
    ok: bool

    def __post_init__(self):
        state = "SUCCESS" if self.ok else "FAILURE"
        logger.debug(f"FutureDefined[{self.future_id}] completed with state: {state}")
        self.status.set(
            value=f"DEFINED:{state}:{datetime_utcnow().isoformat()}",
            expire=FRD_FUTURE_DEFAULT_EXPIRATION
        )
        self.obj.set(
            value=(obj_payload := self.stringify()),
            expire=FRD_FUTURE_DEFAULT_EXPIRATION
        )
        self.bcast_now(item=obj_payload, ignore_flag=False)
        match self.value:
            case EitherMonad.Right(value=value):
                # TODO: Consider using a more robust serialization method...
                # TODO: Should we consider collapsing nested-futures? i.e., Future[Future[A]] => Future[A]
                payload = json.dumps(value)
                self.output.set(
                    value=payload,
                    expire=FRD_FUTURE_DEFAULT_EXPIRATION
                )
            case EitherMonad.Left(exception=exception):
                payload = json.dumps({"error": str(exception)})
                self.output.set(
                    value=str(exception),
                    expire=FRD_FUTURE_DEFAULT_EXPIRATION
                )

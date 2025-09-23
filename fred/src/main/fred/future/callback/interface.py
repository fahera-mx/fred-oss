from threading import Thread
from typing import (
    Generic,
    TypeVar,
    Optional,
)

from fred.settings import logger_manager
from fred.monad.catalog import EitherMonad

logger = logger_manager.get_logger(__name__)

A = TypeVar("A")


class CallbackInterface(Generic[A]):
    
    def _on_start(self, future_id: str):
        raise NotImplementedError
    
    def _on_complete(self, future_id: str, output: EitherMonad.Either[A]):
        raise NotImplementedError
    
    def run(self, future_id: str, blocking: bool = False, output: Optional[EitherMonad.Either[A]] = None) -> Optional[Thread]:
        """Executes the callback with the provided output and handles any exceptions.
        Args:
            output (EitherMonad.Either[A]): The output to be passed to the callback.
        Returns:
            bool: True if the callback executed successfully, False otherwise.
        """
        # TODO: Consider using a richer return type to capture more details about the execution
        #  and optionally propagate the callback return value.
        try:
            match output:
                case None:
                    thread = Thread(
                        target=lambda: self._on_start(future_id=future_id),
                        daemon=True
                    )
                case EitherMonad.Either():
                    thread = Thread(
                        target=lambda: self._on_complete(future_id=future_id, output=output),
                        daemon=True
                    )
            thread.start()
            if blocking:
                thread.join()
            return thread
        except Exception as e:
            logger.error(f"Callback execution failed on future '{future_id}': {e}")
            return None

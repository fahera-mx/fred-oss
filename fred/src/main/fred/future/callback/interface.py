from typing import (
    Generic,
    TypeVar,
)

from fred.settings import logger_manager
from fred.monad.catalog import EitherMonad

logger = logger_manager.get_logger(__name__)

A = TypeVar("A")


class CallbackInterface(Generic[A]):
    
    def execute(self, future_id: str, output: EitherMonad.Either[A]):
        raise NotImplementedError()
    
    def run(self, future_id: str, output: EitherMonad.Either[A]) -> bool:
        """Executes the callback with the provided output and handles any exceptions.
        Args:
            output (EitherMonad.Either[A]): The output to be passed to the callback.
        Returns:
            bool: True if the callback executed successfully, False otherwise.
        """
        # TODO: Consider using a richer return type to capture more details about the execution
        #  and optionally propagate the callback return value.
        try:
            self.execute(future_id=future_id, output=output)
            return True
        except Exception as e:
            logger.error(f"Callback execution failed on future '{future_id}': {e}")
            return False

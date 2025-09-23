from typing import (
    Any,
    Callable,
    TypeVar,
)

from fred.future.callback.interface import CallbackInterface
from fred.monad.catalog import EitherMonad

A = TypeVar("A")


class CallbackFunction(CallbackInterface[A]):
    
    def __init__(self, function: Callable[[EitherMonad.Either[A]], None], **kwargs):
        self.function = function
        self.kwargs = kwargs

    def _on_start(self, future_id: str) -> Any:
        return self.function(
            future_id=future_id,
            **self.kwargs
        )

    def _on_complete(self, future_id: str, output: EitherMonad.Either[A]) -> Any:
        return self.function(
            output=output,
            future_id=future_id,
            **self.kwargs
        )

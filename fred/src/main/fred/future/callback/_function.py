from typing import (
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

    def execute(self, future_id: str, output: EitherMonad.Either[A]):
        self.function(output, **self.kwargs)

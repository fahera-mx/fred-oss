from typing import (
    Callable,
    Generic,
    TypeVar,
)

A = TypeVar("A")
B = TypeVar("B")


class MonadInterface(Generic[A]):
    
    @classmethod
    def from_value(cls, val: A) -> 'MonadInterface[A]':
        raise NotImplementedError
    
    def flat_map(self, function: Callable[[A], 'MonadInterface[B]']) -> 'MonadInterface[B]':
        raise NotImplementedError

    def map(self, function: Callable[[A], B]) -> 'MonadInterface[B]':
        # Map can be implemented using flat_map to avoid code duplication and ensure consistency
        return self.flat_map(function=lambda value: type(self).from_value(function(value)))

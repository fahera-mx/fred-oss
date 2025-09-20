from dataclasses import dataclass
from functools import wraps
from typing import (
    Callable,
    Generic,
    TypeVar,
)

from fred.settings import logger_manager

logger = logger_manager.get_logger(__name__)

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
        return self.flat_map(function=lambda value: self.__class__[B].from_value(val=function(value)))

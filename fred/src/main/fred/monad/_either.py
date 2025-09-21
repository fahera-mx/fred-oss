from dataclasses import dataclass
from functools import wraps
from typing import (
    Callable,
    Generic,
    Generator,
    TypeVar,
)

from fred.settings import logger_manager
from fred.monad.interface import MonadInterface

logger = logger_manager.get_logger(__name__)

A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True, slots=True)
class EitherWrapper(Generic[A]):
    function: Callable[..., A]

    def __call__(self, *args, **kwargs) -> A:
        return self.function(*args, **kwargs)

    def either(self, *args, **kwargs)-> 'Either[A]':
        try:
            return Right[A].from_value(val=self.function(*args, **kwargs))
        except Exception as e:
            return Left(exception=e)


class Either(MonadInterface[A]):

    @classmethod
    def comprehension(cls, generator: Generator):
        try:
            return Either.from_value(val=next(generator))
        except Exception as e:
            return Left(exception=e)

    @classmethod
    def decorator(cls, function: Callable):
        return wraps(function, updated=())(EitherWrapper(function=function))

    @classmethod
    def from_value(cls, val: A) -> 'Either[A]':
        if isinstance(val, Exception):
            return Left(exception=val)
        return Right(value=val)

    def resolve(self) -> A:
        match self:
            case Right(value=value):
                return value
            case Left(exception=exception):
                raise exception
            case _:
                raise TypeError("Unknown Either type")
            
    def __iter__(self) -> Generator[A, None, None]:
        match self:
            case Right(value=value):
                yield from [value]
            case Left(exception=exception):
                logger.warning(f"Attempted to iterate over Left: {exception}")
                yield from []
            case _:
                raise TypeError("Unknown Either type")


@dataclass(frozen=True, slots=True)
class Right(Either[A]):
    value: A

    def flat_map(self, function: Callable[[A], Either[B]]) -> Either[B]:
        try:
            return function(self.value)
        except Exception as e:
            logger.exception(f"Error in flat_map: {e}")
            # Consider that a right that fails is a left
            return Left(exception=e)


@dataclass(frozen=True, slots=True)
class Left(Either[A]):
    exception: Exception

    def flat_map(self, function: Callable[[A], Either[B]]) -> Either[B]:
        return Left(exception=self.exception)  # Propagate exception
    
    def map(self, function: Callable[[A], B]) -> Either[B]:
        return Left(exception=self.exception)  # Propagate exception


class EitherMonad(Either[A]):
    Either = Either
    Left = Left
    Right = Right

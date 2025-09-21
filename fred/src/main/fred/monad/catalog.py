import enum

from fred.monad._either import EitherMonad


class MonadCatalog(enum.Enum):
    """Enum representing the different types of Monads."""
    EITHER = EitherMonad

    def __call__(self, *args, **kwargs):
        return self.value.from_value(*args, **kwargs)

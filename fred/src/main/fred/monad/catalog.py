import enum

from fred.monad._either import Either, Left, Right


class MonadCatalog(enum.Enum):
    """Enum representing the different types of Monads."""
    EITHER = type("Either", (Either,), {"Left": Left, "Right": Right})

    def __call__(self, *args, **kwargs):
        return self.value.from_value(*args, **kwargs)

import enum

from fred.future.callback.interface import CallbackInterface
from fred.future.callback._function import CallbackFunction



class CallbackCatalog(enum.Enum):
    FUNCTION = CallbackFunction

    def __call__(self, *args, **kwargs) -> CallbackInterface:
        return self.value(*args, **kwargs)

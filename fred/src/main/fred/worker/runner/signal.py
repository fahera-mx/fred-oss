from enum import Enum, auto

from fred.dao.comp.catalog import FredQueue


class RunnerSignal(Enum):
    """Signals used for controlling the runner process."""
    STOP = auto()
    PING = auto()

    def send(self, queue: FredQueue):
        """Send the signal to the specified queue."""
        return queue.add(item=self.name)

from enum import Enum, auto

from fred.utils.dateops import datetime_utcnow


class RunnerStatus(Enum):
    """Statuses used for tracking the runner process."""
    UNDEFINED = auto()
    STARTED = auto()
    STOPPED = auto()
    RUNNING = auto()
    ERROR = auto()

    @staticmethod
    def get_key(runner_id: str) -> str:
        """Get the status key for the specified runner ID."""
        return f"frd:runner:{runner_id}"
    
    def get_val(self, queue_slug: str, *include) -> str:
        """Get the string representation of the status."""
        return ":".join([queue_slug, self.name, datetime_utcnow().isoformat(), *include]) 
    
    @classmethod
    def parse_value(cls, value: str) -> tuple[str, "RunnerStatus"]:
        """Parse the status from the stored value."""
        queue_slug, status, *_ = value.split(":")
        return (queue_slug, cls[status.upper()])

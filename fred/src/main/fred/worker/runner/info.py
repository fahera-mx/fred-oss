import uuid
from typing import Optional
from dataclasses import dataclass

from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RunnerInfo:
    runner_id: str
    created_at: str
    runner_inner_handler_classname: str
    runner_inner_handler_classpath: str
    lifetime: int
    timeout: int

    @classmethod
    def create(
        cls,
        runner_inner_handler_classname: str,
        runner_inner_handler_classpath: str,
        runner_id: Optional[str] = None,
        created_at: Optional[str] = None,
        lifetime: int = 3600,  # Default to 1 hour
        timeout: int = 10,  # Default to 10 seconds
    ) -> "RunnerInfo":
        from fred.utils.dateops import datetime_utcnow
        return cls(
            runner_id=runner_id or str(uuid.uuid4()),
            runner_inner_handler_classname=runner_inner_handler_classname,
            runner_inner_handler_classpath=runner_inner_handler_classpath,
            created_at=created_at or datetime_utcnow().isoformat(),
            lifetime=lifetime,
            timeout=timeout,
        )

    def get_start_event(self, **kwargs) -> dict:
        runner_id = kwargs.pop("runner_id", self.runner_id) 
        payload = {
            "lifetime": self.lifetime,
            "timeout": self.timeout,
            "runner_configs": {
                "id": runner_id,
                "import_pattern": self.runner_inner_handler_classpath,
                "handler_classname": self.runner_inner_handler_classname,
            },
            **kwargs,
        }
        return {
            "input": payload,
            "id": runner_id,
        }

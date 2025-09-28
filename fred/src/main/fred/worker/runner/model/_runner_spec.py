import uuid
from dataclasses import dataclass

from fred.settings import logger_manager
from fred.utils.dateops import datetime_utcnow
from fred.worker.runner.model._handler import Handler
from fred.worker.runner.model.interface import ModelInterface
from fred.worker.runner.settings import (
    FRD_RUNNER_REQUEST_QUEUE,
    FRD_RUNNER_RESPONSE_QUEUE,
)

logger = logger_manager.get_logger(name=__name__)



@dataclass(frozen=True, slots=False)
class RunnerSpec(ModelInterface):
    runner_id: str
    created_at: str
    queue_slug: str
    inner: Handler
    use_response_queue: bool = False
    lifetime: int = 3600  # Default to 1 hour if not specified
    timeout: int = 30  # Default to 30 seconds if not specified

    @classmethod
    def auto(cls, **kwargs) -> "RunnerSpec":
        kwargs["runner_id"] = kwargs.get("runner_id", str(uuid.uuid4()))
        return cls.from_payload(payload=kwargs)

    @classmethod
    def from_payload(cls, payload: dict) -> "RunnerSpec":
        inner_handler_kwargs = {
            "classname": payload.pop("handler_classname", None) or (
                logger.warning("No handler_classname provided; defaulting to: 'HandlerInterface'")
                or "HandlerInterface"
            ),
            "classpath": payload.pop("handler_classpath", None) or (
                logger.warning("No handler_classpath provided; defaulting to: 'fred.worker.interface'")
                or "fred.worker.interface"
            ),
            "kwargs": payload.pop("handler_kwargs", {}),
            **payload.pop("handler_configs", {})
        }
        runner_id = payload.pop("runner_id", None) or (
            logger.warning("No runner_id provided; generating a new one using UUID4.")
            or str(uuid.uuid4())
        )
        return cls(
            runner_id=runner_id,
            created_at=datetime_utcnow().isoformat(),
            queue_slug=payload.pop("queue_slug", None) or (
                logger.warning("Queue slug not specified; defaulting to: 'demo'")
                or "demo"
            ),
            inner=Handler(**inner_handler_kwargs),
            use_response_queue=payload.pop("use_response_queue", False),
            lifetime=payload.pop("lifetime", 3600),
            timeout=payload.pop("timeout", 30),
        )
    
    def as_dict(self) -> dict:
        return {
            "runner_id": self.runner_id,
            "created_at": self.created_at,
            "queue_slug": self.queue_slug,
            "handler_classname": self.inner.classname,
            "handler_classpath": self.inner.classpath,
            "handler_kwargs": self.inner.kwargs,
            "use_response_queue": self.use_response_queue,
            "lifetime": self.lifetime,
            "timeout": self.timeout,
        }
    
    def as_event(self, drop_id: bool = False) -> dict:
        event = {"input": self.as_dict()}
        if not drop_id:
            event["id"] = self.runner_id
        return event
    
    @property
    def request_queue_name(self) -> str:
        return FRD_RUNNER_REQUEST_QUEUE or f"req:{self.queue_slug}"
    
    @property
    def response_queue_name(self) -> str:
        return FRD_RUNNER_RESPONSE_QUEUE or f"res:{self.queue_slug}"

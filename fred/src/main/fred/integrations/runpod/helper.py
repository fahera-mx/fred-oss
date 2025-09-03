import time
from dataclasses import dataclass, field
from typing import Optional

from fred.utils.dateops import datetime_utcnow
from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class HandlerHelper:
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.metadata["handler_created_at"] = datetime_utcnow().isoformat()

    @classmethod
    def find_handler(
            cls,
            import_pattern: str,
            handler_classname: str,
            **init_kwargs,
    ) -> 'HandlerHelper':
        import importlib

        # Dynamically import the handler class
        handler_module = importlib.import_module(import_pattern)
        handler_cls = getattr(handler_module, handler_classname)
        # Ensure the handler class exists and is a subclass of HandlerHelper
        if not handler_cls or not issubclass(handler_cls, cls):
            logger.error(f"Handler class '{handler_classname}' not found or is not a subclass of HandlerHelper.")
            raise ValueError(f"Handler '{handler_classname}' not found in module '{import_pattern}' or is not a subclass of HandlerHelper.")
        kwargs = {
            "metadata": {
                "handler_found_at": datetime_utcnow().isoformat()
            },
            **init_kwargs,
        }
        return handler_cls(**kwargs)

    def handler(self, payload: dict) -> Optional[dict]:
        logger.warning("Handler method not implemented.")
        return payload

    def run(self, event: dict) -> dict:
        job_event_identifier = event.get("id")
        self.metadata["run_seq"] = self.metadata.get("run_seq", 0) + 1
        payload = event.get("input", {})
        started_at = datetime_utcnow().isoformat()
        start_time = time.perf_counter()
        ok = True
        try:
            response = self.handler(payload=payload)
        except Exception as e:
            ok = False
            logger.error(f"Error processing event {job_event_identifier}: {e}")
            response = {
                "error": str(e)
            }
        return {
            "ok": ok,
            "id": job_event_identifier,
            "duration": time.perf_counter() - start_time,
            "started_at": started_at,
            "response": response,
            "metadata": self.metadata,
        }

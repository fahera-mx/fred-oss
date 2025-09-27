import uuid
import json
from typing import Optional

from pydantic.dataclasses import dataclass

from fred.dao.comp.catalog import FredQueue
from fred.worker.runner.model.interface import ModelInterface


@dataclass(frozen=True, slots=True)
class RunnerRequest(ModelInterface):
    request_id: str
    payload: dict

    @classmethod
    def uuid(
            cls,
            payload: dict,
            uuid_hash: bool = False,
            request_id: Optional[str] = None,
    ) -> "RunnerRequest":
        request_id = request_id or (
            str(uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(payload, default=str)))
            if uuid_hash else str(uuid.uuid4())
        )
        return cls(request_id=request_id, payload=payload)
    
    def as_payload(self) -> dict:
        return {
            "request_id": self.request_id,
            **self.payload,
        }
    
    def dispatch(self, request_queue: FredQueue, **kwargs):
        serialization_kwargs = {
            "default": str,
            **kwargs
        }
        request = json.dumps(self.as_payload(), **serialization_kwargs)
        return request_queue.add(request)

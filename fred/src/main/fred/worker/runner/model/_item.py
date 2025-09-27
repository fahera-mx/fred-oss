import json
import uuid
from typing import Optional

from pydantic.dataclasses import dataclass

from fred.utils.dateops import datetime_utcnow
from fred.worker.runner.model._request import RunnerRequest
from fred.worker.runner.model.interface import ModelInterface


@dataclass(frozen=True, slots=True)
class RunnerItem(ModelInterface):
    item_id: str
    item_created_at: str
    item_payload: dict

    @classmethod
    def uuid(cls, payload: dict, uuid_hash: bool = False) -> "RunnerItem":
        item_id = payload.get("item_id") or (
            str(uuid.uuid5(uuid.NAMESPACE_DNS, json.dumps(payload, default=str)))
            if uuid_hash else str(uuid.uuid4())
        )
        return cls(
            item_id=item_id,
            item_created_at=datetime_utcnow().isoformat(),
            item_payload=payload
        )
    
    def as_payload(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_created_at": self.item_created_at,
            **self.item_payload,
        }
    
    def as_request(
            self,
            use_hash: bool = False,
            request_id: Optional[str] = None
    ) -> RunnerRequest:
        return RunnerRequest.uuid(
            payload=self.as_payload(),
            request_id=request_id,
            uuid_hash=use_hash,
        )

import uuid
import json
from dataclasses import dataclass

from fred.settings import (
    get_environ_variable,
    logger_manager,
)
from fred.worker.runner.utils import (
    get_request_queue_name_from_payload,
    get_response_queue_name_from_payload,
    get_redis_configs_from_payload,
)

from redis import Redis

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RunnerClient:
    instance: Redis
    req_queue: str
    res_queue: str

    @classmethod
    def auto(cls, **kwargs) -> "RunnerClient":
        redis_configs = get_redis_configs_from_payload(payload=kwargs, keep=False)
        redis_instance = Redis(**redis_configs)
        req_queue = get_request_queue_name_from_payload(payload=kwargs, keep=False) 
        res_queue = get_response_queue_name_from_payload(payload=kwargs, keep=False) or (
            logger.warning("Redis response queue not specified; defaulting to inferring pattern.")
            or f"res:{req_queue.split(':')[-1]}"
        )
        logger.info(f"Connecting to Redis, using request queue '{req_queue}' and response queue '{res_queue}'.")
        return cls(
            instance=redis_instance,
            req_queue=req_queue,
            res_queue=res_queue,
        )

    @property
    def PING(self):
        return self.signal("PING")

    @property
    def STOP(self):
        return self.signal("STOP")

    def signal(self, signal: str):
        # TODO: Validate signals via enum
        self.instance.lpush(self.req_queue, signal)

    def send(self, item: dict, uuid_hash: bool = False) -> str:
        item_id = item.get("item_id")
        item_str = json.dumps(item)
        if not item_id:
            logger.warning("Item does not have 'item_id'; assigning a UUID based on the hash.")
            item["item_id"] = item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item_str)) \
                if uuid_hash else str(uuid.uuid4())
            item_str = json.dumps(item)
        self.instance.lpush(self.req_queue, item_str)
        self.instance.set(f"item_status:{item_id}", "IN_QUEUE")
        return item_id
    
    def fetch_status(self, item_id: str) -> str | None:
        status_raw = self.instance.get(f"item_status:{item_id}")
        if not status_raw:
            logger.info(f"No status found for item_id '{item_id}'.")
            return None
        return status_raw.decode("utf-8")

    def fetch_result(self, item_id: str, blocking: bool = False) -> dict | None:
        match self.fetch_status(item_id=item_id):
            case None:
                logger.info(f"No status found for item_id '{item_id}'.")
                return None
            case "IN_QUEUE" | "PROCESSING":
                if blocking:
                    logger.info(f"Blocking until item '{item_id}' is completed.")
                    while (status := self.fetch_status(item_id=item_id)) in ("IN_QUEUE", "PROCESSING"):
                        continue
                else:
                    logger.info(f"Item '{item_id}' is still in progress (current status: '{self.fetch_status(item_id=item_id)}').")
                    return None
            case "FAILED":
                logger.error(f"Item '{item_id}' processing failed.")
                return None
            case "COMPLETED":
                result_raw = self.instance.get(f"item_output:{item_id}")
                if result_raw:
                    try:
                        return json.loads(result_raw)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON result for item_id '{item_id}': {e}")
                        return None
                else:
                    logger.error(f"No result found for item_id '{item_id}'.")
                    return None
            case status:
                logger.warning(f"Item '{item_id}' has unrecognized status '{status}'. Proceeding to fetch result.")

import uuid
import json
from dataclasses import dataclass

from fred.utils.dateops import datetime_utcnow
from fred.worker.interface import HandlerInterface
from fred.settings import (
    get_environ_variable,
    logger_manager,
)
from fred.worker.runner.utils import (
    get_request_queue_name_from_payload,
    get_response_queue_name_from_payload,
)

from redis import Redis

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=False)
class RunnerHandler(HandlerInterface):
    
    def __post_init__(self):
        super().__post_init__()
        logger.info("Runpod Handler initialized using Fred-Worker interface.")

    def handler(self, payload: dict) -> dict:
        # TODO: Breakdown the handler logic into smaller methods for better readability and testing
        # E.g., loop method, process item method, signal handling method, etc.
        lifespan = payload.get("lifetime", 3600)  # Default to 1 hour if not specified
        timeout = payload.get("timeout", 30)  # Default to 30 seconds if not specified
        # Get Redis connection details from payload or environment variables
        redis_configs = {
            "host": get_environ_variable(name="REDIS_HOST", default="localhost"),
            "port": int(get_environ_variable(name="REDIS_PORT", default=6379)),
            "password": get_environ_variable(name="REDIS_PASSWORD", default=None),
            "db": int(get_environ_variable(name="REDIS_DB", default=0)),
            "decode_responses": True,
            **payload.pop("redis_configs", {}),
        }
        # Connect to Redis
        redis = Redis(**redis_configs)
        req_queue = get_request_queue_name_from_payload(payload=payload, keep=False) 
        res_queue = get_response_queue_name_from_payload(payload=payload, keep=False)
        # Handoff to target handler (i.e., runner)
        runner_configs = payload.pop("runner_configs")
        runner_id = runner_configs.pop("id", str(uuid.uuid4()))
        runner = HandlerInterface.find_handler(**runner_configs)
        logger.info(f"Runpod Redis Handler started with runner '{runner_id}' listening to Redis queue: '{req_queue}'")
        redis.set(f"runner_status:{runner_id}", "RUNNING")
        redis.set(f"runner_created_at:{runner_id}", datetime_utcnow().isoformat())
        # Main runner loop to process items from Redis queue
        # TODO: Can we make this main-loop concurrent with threads or async?
        # TODO: Consider collecting metrics (e.g., processing time per item, total items processed, errors, etc.) and stats
        start_time = datetime_utcnow()
        last_processed_time = datetime_utcnow()
        while (elapsed_seconds := (datetime_utcnow() - start_time).total_seconds()):
            if elapsed_seconds > lifespan:
                logger.info("Lifespan exceeded; exiting runner loop.")
                break
            if (idle_seconds := (datetime_utcnow() - last_processed_time).total_seconds()) > timeout:
                logger.info(f"Idle time ({idle_seconds}) exceeded timeout ({timeout}); exiting runner loop.")
                break
            # Fetch item from Redis queue 
            try:
                item_str = redis.rpop(req_queue)
            except Exception as e:
                logger.error(f"Error fetching item from Redis queue '{req_queue}': {e}")
                continue
            # If no item, iterate again
            if not item_str:
                continue
            try:
                # Handle special signals
                match item_str:
                    case "STOP" | "SHUTDOWN" | "TERMINATE":
                        logger.info("Received STOP signal; exiting runner loop.")
                        break
                    case "PING":
                        logger.info("Received PING signal; continuing.")
                        last_processed_time = datetime_utcnow()
                        continue
                    case _:
                        pass
                # Parse item payload and extract item_id
                item_payload = json.loads(item_str)
                item_id = item_payload.pop("item_id") or (
                    logger.warning("No item_id provided in payload; generating a new one using UUID5.")
                    or str(uuid.uuid5(uuid.NAMESPACE_OID, item_str))
                )
            except Exception as e:
                logger.error(f"Error decoding or parsing item from Redis: {e}")
                continue
            logger.info(f"Processing item with ID: {item_id}")      
            redis.set(f"item_status:{item_id}", "IN_PROGRESS")
            try:
                out_payload = runner.run(
                    event={
                        "id": item_id,
                        "input": item_payload
                    }
                )
                out_str = json.dumps(out_payload) if isinstance(out_payload, dict) else str(out_payload)
                redis.set(f"item_status:{item_id}", "COMPLETED")
                # TODO: Consider adding a TTL to the result keys (e.g., 24 hours)
                redis.set(f"item_output:{item_id}", out_str)
                if res_queue:
                    redis.lpush(res_queue, out_str) 
            except Exception as e:
                logger.error(f"Error processing item with ID {item_id}: {e}")
                redis.set(f"item_status:{item_id}", "FAILED")
                redis.set(f"item_output:{item_id}", str(e))
                continue
            logger.info(f"Processed item with ID: {item_id}")
            last_processed_time = datetime_utcnow()
        redis.set(f"runner_status:{runner_id}", "STOPPED")
        pending_requests = redis.llen(req_queue)
        if pending_requests:
            logger.warning(f"Runner '{runner_id}' stopped with {pending_requests} pending items still in the queue '{req_queue}'.")
            # TODO: Consider adding logic (optional/configurable) to spin up a new runner to handle pending items or notify runner-manager
        else:
            logger.info("Runner stopped with no pending items in the queue.")
        return {
            "status": "completed",
            "runner_id": runner_id,
            "processed_at": datetime_utcnow().isoformat(),
            "total_elapsed_seconds": (datetime_utcnow() - start_time).total_seconds(),
            "last_processed_at": last_processed_time.isoformat(),
            "idle_seconds": (datetime_utcnow() - last_processed_time).total_seconds(),
            "pending_requests": pending_requests,
            "request_queue": req_queue,
            "response_queue": res_queue,
            "lifespan_seconds": lifespan,
            "timeout_seconds": timeout,
        }

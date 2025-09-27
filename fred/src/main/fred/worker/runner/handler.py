import uuid
import json
from dataclasses import dataclass
from typing import Optional

from fred.future import Future
from fred.monad.catalog import EitherMonad
from fred.utils.dateops import datetime_utcnow
from fred.dao.comp.catalog import FredQueue
from fred.worker.runner.settings import FRD_RUNNER_BACKEND
from fred.worker.runner.backend import RunnerBackend
from fred.worker.runner.model.catalog import RunnerModelCatalog
from fred.worker.interface import HandlerInterface
from fred.worker.runner.status import RunnerStatus

from fred.settings import logger_manager


logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=False)
class RunnerHandler(HandlerInterface):
    
    def __post_init__(self):
        super().__post_init__()
        logger.info("Fred-Runner outer-handler initialized using Fred-Worker interface.")

    @staticmethod 
    def _runner_process(
            item: dict,
            runner: HandlerInterface,
            item_id: str,
            request_id: str,
    ) -> Future[dict]:
        logger.info(f"Processing item '{item_id}' provided by request-id: {request_id}")
        return runner.run(
            event={
                "id": item_id,
                "input": item
            },
            as_future=True,
            future_id=request_id,
        )

    def _runner_loop(
            self,
            runner: HandlerInterface,
            req_queue: FredQueue,
            lifespan: int,
            timeout: int,
            res_queue: Optional[FredQueue] = None,
    ) -> dict:
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
                message = req_queue.pop()
                # If no item, iterate again
                if not message:
                    continue
            except Exception as e:
                logger.error(f"Error fetching item from Redis queue '{req_queue}': {e}")
                continue
            # Handle special signals
            match message:
                case "STOP" | "SHUTDOWN" | "TERMINATE":
                    logger.info("Received STOP signal; exiting runner loop.")
                    break
                case "PING":
                    logger.info("Received PING signal; continuing.")
                    last_processed_time = datetime_utcnow()
                    continue
                case _:
                    pass
            try:
                item = json.loads(message)
                item_id = item.get("item_id") or (
                    logger.warning("No item_id provided in item-payload; generating a new one using UUID5 hash.")
                    or str(uuid.uuid5(uuid.NAMESPACE_OID, message))
                )
                # The request_id is used as the future_id for tracking purposes
                request_id = item.get("request_id") or (
                    logger.warning(f"No request_id provided in item-payload; using the item_id '{item_id}' instead.")
                    or item_id
                )
            except Exception as e:
                logger.error(f"Error decoding or parsing item from Redis: {e}")
                continue
            # Process item using runner and handle result
            future = self._runner_process(item=item, runner=runner, item_id=item_id, request_id=request_id).map(
                lambda res: res if isinstance(res, str) else json.dumps(res, default=str)
            )
            match future.wait():
                case EitherMonad.Right(value):
                    if res_queue:
                        logger.debug(f"Processed item ID '{item_id}' on request ID '{request_id}' and pushed result to response queue.")
                        res_queue.add(value)
                case EitherMonad.Left(error):
                    logger.error(f"Error processing item ID '{item_id}' on request ID '{request_id}': {error}")
                    continue
                case _:
                    logger.error(f"Unexpected result processing item ID '{item_id}' on request ID '{request_id}': {future}")
                    continue
            last_processed_time = datetime_utcnow()
        return {
            "started_at": start_time.isoformat(),
            "stopped_at": datetime_utcnow().isoformat(),
            "total_elapsed_seconds": (datetime_utcnow() - start_time).total_seconds(),
            "last_processed_at": last_processed_time.isoformat(),
            "idle_seconds": (datetime_utcnow() - last_processed_time).total_seconds(),
        }
 

    def handler(self, payload: dict) -> dict:
        # Configure the backend service abstraction (e.g., Redis)
        runner_backend = RunnerBackend.auto(
            service_name=payload.pop("runner_backend", None) or FRD_RUNNER_BACKEND,
            **payload.pop("runner_backend_configs", {}),
        )
        # Outer handler model instance
        spec = RunnerModelCatalog.RUNNER_SPEC.value.from_payload(payload=payload)
        
        # Determine request and response queues to use for this runner instance
        req_queue = runner_backend.queue(name=spec.request_queue_name)
        res_queue = runner_backend.queue(name=spec.response_queue_name) \
            if spec.use_response_queue else None
        # Get runner (inner handler) instance and ID
        # The 'outer' handler delegates the processing of tasks to the 'inner' handler
        # and is responsible for managing the lifecycle and updating the status of the runner
        runner = spec.inner.get_handler()
        runner_id = spec.runner_id
        runner_status = runner_backend.keyval(
            key=RunnerStatus.get_key(runner_id=runner_id)
        )
        logger.info(f"Starting runner with ID '{runner_id}' using request-queue '{req_queue.name}'")
        runner_status.set(
            value=RunnerStatus.STARTED.get_val(),
            expire=None,
        )
        runner_loop = Future(
            function=self._runner_loop,
            runner=runner,
            req_queue=req_queue,
            lifespan=spec.lifetime,
            timeout=spec.timeout,
            res_queue=res_queue,
            # The runner_id is used as the future_id for tracking purposes
            future_id=runner_id,
        )
        runner_status.set(
            value=RunnerStatus.RUNNING.get_val(),
            expire=None,
        )
        results = {
            "runner_id": runner_id,
            "runner_started_at": datetime_utcnow().isoformat(),
            "runner_pending_requests": req_queue.size(),
        }
        match runner_loop.wait():
            case EitherMonad.Right(meta):
                results["runner_status"] = "success"
                results["metadata"] = meta
            case EitherMonad.Left(error):
                results["runner_status"] = "failure"
                results["metadata"] = {
                    "error": str(error)
                }
            case _:
                results["runner_status"] = "unexpected"
                results["metadata"] = {
                    "error": "Unexpected result from runner loop"
                }
        results["pending_requests"] = pending_requests = req_queue.size()
        runner_status.set(
            value=RunnerStatus.STOPPED.get_val(str(pending_requests)),
            expire=3600,  # Keep the stopped status for 1 hour
        )
        if pending_requests:
            logger.warning(f"Runner '{runner_id}' stopped with {pending_requests} pending items still in the queue: '{req_queue.name}'")
        else:
            logger.info(f"Runner '{runner_id}' stopped with no pending items in the queue: '{req_queue.name}'")

        return results

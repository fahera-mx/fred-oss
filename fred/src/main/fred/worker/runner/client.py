import time
from dataclasses import dataclass
from typing import Optional

from fred.future import Future
from fred.future.result import FutureResult
from fred.dao.comp.catalog import FredQueue
from fred.worker.runner.status import RunnerStatus
from fred.worker.runner.signal import RunnerSignal
from fred.worker.runner.backend import RunnerBackend
from fred.worker.runner.model.catalog import RunnerModelCatalog
from fred.worker.runner.settings import (
    FRD_RUNNER_BACKEND,
    FRD_RUNNER_REQUEST_QUEUE,
    FRD_RUNNER_RESPONSE_QUEUE,
)
from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RunnerClient:
    _runner_backend: RunnerBackend
    req_queue: FredQueue
    res_queue: FredQueue


    @classmethod
    def auto(
            cls,
            queue_slug: Optional[str] = None,
            service_name: Optional[str] = None,
            **kwargs
        ) -> "RunnerClient":
        queue_slug = queue_slug or kwargs.pop("queue_slug", None) or (
            logger.warning("Queue slug not specified; defaulting to: 'demo'")
            or "demo"
        )
        queue_name_request = FRD_RUNNER_REQUEST_QUEUE or f"req:{queue_slug}"
        queue_name_response = FRD_RUNNER_RESPONSE_QUEUE or f"res:{queue_slug}"
        runner_backend = RunnerBackend.auto(
            service_name=service_name or FRD_RUNNER_BACKEND,
            **kwargs
        )
        return cls(
            _runner_backend=runner_backend,
            req_queue=runner_backend.queue(name=queue_name_request),
            res_queue=runner_backend.queue(name=queue_name_response),
        )

    @property
    def PING(self):
        return self.signal(RunnerSignal.PING)

    @property
    def STOP(self):
        return self.signal(RunnerSignal.STOP)

    def signal(self, signal: str | RunnerSignal):
        signal = RunnerSignal[signal.upper()] if isinstance(signal, str) else signal
        return signal.send(self.req_queue)

    def runner_status(self, runner_id: str) -> RunnerStatus:
        runner_status=self._runner_backend.keyval(
                key=RunnerStatus.get_key(runner_id=runner_id)
            )
        if not (value := runner_status.get()):
            logger.warning(f"No status found for runner_id: '{runner_id}'")
            return RunnerStatus.UNDEFINED
        return RunnerStatus.parse_value(value=value)

    def send(
            self,
            item: dict,
            req_uuid_hash: bool = False,
            item_uuid_hash: bool = False,
    ) -> str:
        item_instance = RunnerModelCatalog.ITEM.value.uuid(payload=item, uuid_hash=item_uuid_hash)
        request = item_instance.as_request(
            use_hash=req_uuid_hash,
            request_id=item.get("request_id"),
        )
        request.dispatch(request_queue=self.req_queue)
        return request.request_id
    
    @staticmethod
    def fetch_status(request_id: str) -> Optional[str]:
        return FutureResult._get_status_key(future_id=request_id).get()

    def _pullsync(
            self,
            request_id: str,
            retry_sync: int = 10,
            retry_delay: float = 0.2,
            retry_backoff_rate: float = 0.1,
            **kwargs,
    ):
        from fred.future.utils import pull_future_result

        if not self._is_ready_for_pullsync(
                request_id=request_id,
                retry_sync=retry_sync,
                retry_delay=retry_delay,
                retry_backoff_rate=retry_backoff_rate,
                # Always fail in pullsync to raise an exception if not ready.
                # In addition, this will be caught by the Future to propagate the exception.
                fail=True,
        ):
            raise ValueError(f"The provided request_id '{request_id}' is not ready for pullsync.")

        return pull_future_result(
            future_id=request_id,
            retry_delay=retry_delay,
            retry_backoff_rate=retry_backoff_rate,
            **kwargs
        )

    def pullsync(
            self,
            request_id: str,
            retry_sync: int = 10,
            retry_delay: float = 0.2,
            retry_backoff_rate: float = 0.1,
            **kwargs,
    ) -> Future:
        return Future(
            function=self._pullsync,
            request_id=request_id,
            retry_sync=retry_sync,
            retry_delay=retry_delay,
            retry_backoff_rate=retry_backoff_rate,
            **kwargs
        )

    def _is_ready_for_pullsync(
            self,
            request_id: str,
            retry_sync: int = 10,
            retry_delay: float = 0.2,
            retry_backoff_rate: float = 0.1,
            fail: bool = False,
    ) -> bool:
        if not self.fetch_status(request_id=request_id):
            logger.info(f"No status found for request_id '{request_id}'")
            retry_kwargs = {
                "request_id": request_id,
                "retry_sync": retry_sync - 1,
                "retry_delay": retry_delay * (1 + retry_backoff_rate),  # Exponential backoff
                "retry_backoff_rate": retry_backoff_rate,
                "fail": fail,
            }
            if retry_sync:
                time.sleep(retry_delay)
                return self._is_ready_for_pullsync(**retry_kwargs)
            elif fail:
                logger.error(f"Failed to fetch status for request_id '{request_id}' after retries.")
                raise ValueError(f"No status found for request_id '{request_id}'")
            else:
                return False
        return True

    def fetch_result(self, request_id: str, now: bool = False, timeout: Optional[float] = None, **kwargs) -> Optional[dict]:
        future = self.pullsync(request_id=request_id, **kwargs)
        if now:
            return future.getwhatevernow()
        return future.wait_and_resolve(timeout=timeout)

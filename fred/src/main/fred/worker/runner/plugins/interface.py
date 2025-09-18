from dataclasses import dataclass
from threading import Thread
from typing import Optional

from redis import Redis

from fred.settings import logger_manager
from fred.worker.runner.info import RunnerInfo
from fred.worker.runner.handler import RunnerHandler
from fred.worker.runner.utils import get_redis_configs_from_payload
from fred.utils.dateops import datetime_utcnow

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class PluginInterface:
    """Interface for the different plugins available for FRED Runners."""
    redis: Redis

    @classmethod
    def auto(cls, **kwargs) -> "PluginInterface":
        redis = kwargs.pop("instance", None) or Redis(**get_redis_configs_from_payload(payload=kwargs, keep=False))
        return cls(redis=redis)

    def _execute(
            self,
            runner_info: RunnerInfo,
            outer_handler: RunnerHandler,
            **kwargs
        ):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def _monitor(self, runner_info: RunnerInfo, **kwargs):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def monitor(
            self,
            runner_info: RunnerInfo,
            blocking: bool = False,
            timeout: Optional[int] = None,
            **kwargs
        ) -> Optional[Thread]:
        # Start monitoring in a separate thread
        thread = Thread(
            target=self._monitor,
            kwargs={
                "runner_info": runner_info,
                "blocking": blocking,
                **kwargs
            },
            daemon=True,
        )
        thread.start()
        # If blocking is True, wait for the thread to finish or timeout
        return thread.join(timeout=timeout) if blocking else thread

    def _execute_wrapper(
            self,
            runner_info: RunnerInfo,
            outer_handler: RunnerHandler,
            **kwargs
        ) -> str:
        runner_id = runner_info.runner_id
        self.redis.set(f"runner:{runner_id}:status", f"STARTING:{datetime_utcnow().isoformat()}")
        try:
            self._execute(
                    runner_info=runner_info,
                    outer_handler=outer_handler,
                    **kwargs
                )
        except Exception as e:
            self.redis.set(f"runner:{runner_id}:status", f"ERROR:{datetime_utcnow().isoformat()}")
            logger.error(f"Error executing runner '{runner_id}': {e}")
            raise
        return runner_id

    def execute(
            self,
            runner_info: RunnerInfo,
            outer_handler: RunnerHandler,
            wait_for_exec: bool = False,
            timeout: Optional[int] = None,
            enable_monitor: bool = False,
            wait_for_monitor: bool = False,
            **kwargs
        ) -> Thread:
        runner_id = runner_info.runner_id
        logger.info(f"Starting thread runner '{runner_id}' using plugin '{self.__class__.__name__}'.")
        thread = Thread(
            target=self._execute_wrapper,
            kwargs={
                "runner_info": runner_info,
                "outer_handler": outer_handler,
                **kwargs
            },
            daemon=True,
        )
        thread.start()
        if enable_monitor:
            self.monitor(
                runner_info=runner_info,
                blocking=wait_for_monitor,
                timeout=timeout,
                **kwargs
            )
        else:
            logger.info(f"Monitoring disabled for runner '{runner_id}'.")
        if wait_for_exec:
            logger.info(f"Waiting for execution of runner '{runner_id}' to complete.")
            thread.join()
        return thread

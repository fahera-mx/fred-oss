from dataclasses import dataclass
from threading import Thread
from typing import Optional

from fred.future import Future
from fred.settings import logger_manager
from fred.utils.dateops import datetime_utcnow
from fred.worker.runner.status import RunnerStatus
from fred.worker.runner.model._runner_spec import RunnerSpec
from fred.worker.runner.backend import RunnerBackend
from fred.worker.runner.settings import FRD_RUNNER_BACKEND


logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class PluginExecutionOutput:
    runner_id: str
    future_exec: Future
    future_monitor: Optional[Future] = None


@dataclass(frozen=True, slots=True)
class PluginInterface:
    backend: RunnerBackend

    @classmethod
    def auto(cls, service_name: Optional[str] = None, **kwargs) -> "PluginInterface":
        """Auto-instantiate the plugin interface with backend services.
        If a backend service is not provided, it will create one using configurations
        extracted from the provided keyword arguments.
        Args:
            **kwargs: Keyword arguments that may contain backend service configurations or an existing backend instance.
        Returns:
            PluginInterface: An instance of the PluginInterface with backend services.
        """
        backend = RunnerBackend.auto(
            service_name=service_name or FRD_RUNNER_BACKEND,
            **kwargs
        )
        return cls(backend=backend)
    
    def _execute(
            self,
            spec: RunnerSpec,
            **kwargs
        ):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def _monitor(self, spec: RunnerSpec, **kwargs):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def _execute_wrapper(
            self,
            spec: RunnerSpec,
            **kwargs
        ) -> str:
        """Wrapper method to handle execution and include error logging.

        Since we don't control the implementation of the _execute method in subclasses, we
        need to wrap it to add error handling and logging.

        Args:
            runner_info (RunnerInfo): Information about the runner to execute.
            outer_handler (RunnerHandler): The outer handler to use for execution.
            **kwargs: Additional keyword arguments to pass to the execution method implemented by the subclass.
        """
        runner_id = spec.runner_id
        runner_status = self.backend.keyval(
            key=RunnerStatus.get_key(runner_id=runner_id)
        )
        try:
            self._execute(spec=spec, **kwargs)
        except Exception as e:
            runner_status.set(RunnerStatus.ERROR.get_val(str(e)))
            logger.error(f"Error executing runner '{runner_id}': {e}")
            raise
        return runner_id
    
    def execute(
            self,
            spec: RunnerSpec,
            wait_for_exec: bool = False,
            wait_for_monitor: bool = False,
            timeout: Optional[int] = None,
            enable_monitor: bool = False,
            **kwargs
        ) -> PluginExecutionOutput:
        runner_id = spec.runner_id
        logger.info(f"Starting thread runner '{runner_id}' using plugin '{self.__class__.__name__}'.")
        future_exec = Future(
            function=self._execute_wrapper,
            spec=spec,
            **kwargs
        )
        future_monitor = None
        if enable_monitor:
            future_monitor = self.monitor(spec=spec, **kwargs)
        else:
            logger.info(f"Monitoring disabled for runner '{runner_id}'.")
        if wait_for_exec:
            logger.info(f"Waiting for execution of runner '{runner_id}' to complete.")
            future_exec.wait(timeout=timeout)
        if future_monitor and wait_for_monitor:
            future_monitor.wait(timeout=timeout)
        return PluginExecutionOutput(
            runner_id=runner_id,
            future_exec=future_exec,
            future_monitor=future_monitor,
        )
    
    def monitor(
            self,
            spec: RunnerSpec,
            **kwargs
        ) -> Optional[Thread]:
        """Start monitoring the runner in a separate thread.
        Args:
            runner_info (RunnerInfo): Information about the runner to monitor.
            blocking (bool, optional): Whether to block the main thread until monitoring is complete. Defaults to False.
            timeout (Optional[int], optional): Timeout in seconds for the monitoring thread. Defaults to None.
            **kwargs: Additional keyword arguments to pass to the monitoring method.
        Returns:
            Optional[Thread]: The thread object for the monitoring thread if not blocking, else None."""
        # Start monitoring in a separate thread
        return Future(
            function=self._monitor,
            spec=spec,
            **kwargs
        )

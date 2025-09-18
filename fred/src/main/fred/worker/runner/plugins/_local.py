from dataclasses import dataclass

from fred.settings import logger_manager
from fred.worker.runner.info import RunnerInfo
from fred.worker.runner.handler import RunnerHandler
from fred.worker.runner.plugins.interface import PluginInterface

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class LocalPlugin(PluginInterface):

    def _execute(
            self,
            runner_info: RunnerInfo,
            outer_handler: RunnerHandler,
            **kwargs
        ):
        """Execute the runner locally using the provided outer handler.
        Args:
            runner_info (RunnerInfo): Information about the runner to execute.
            outer_handler (RunnerHandler): The outer handler to use for execution.
            **kwargs: Additional keyword arguments to pass to the execution method implemented by the subclass.
        """
        outer_handler.run(event=runner_info.get_start_event(**kwargs))

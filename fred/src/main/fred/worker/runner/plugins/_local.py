from dataclasses import dataclass

from fred.settings import logger_manager
from fred.worker.runner.handler import RunnerHandler
from fred.worker.runner.model._runner_spec import RunnerSpec
from fred.worker.runner.plugins.interface import PluginInterface

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class LocalPlugin(PluginInterface):

    def _execute(
            self,
            spec: RunnerSpec,
            **kwargs
        ):
        """Execute the runner locally by directly invoking the handler's run method.
        This method bypasses any queuing mechanism and runs the handler in the current process.
        Args:
            spec (RunnerSpec): The specification of the runner to execute.
            **kwargs: Additional keyword arguments that may be used for execution.
        """
        outer_handler_classname = kwargs.pop("outer_handler_classname", "RunnerHandler")
        outer_handler_classpath = kwargs.pop("outer_handler_classpath", "fred.worker.runner.handler")
        outer_handler_init_kwargs = kwargs.pop("outer_handler_init_kwargs", {})
        outer_handler = RunnerHandler.find_handler(
            handler_classname=outer_handler_classname,
            import_pattern=outer_handler_classpath,
            **outer_handler_init_kwargs,
        )
        return outer_handler.run(event=spec.as_event(), as_future=False)

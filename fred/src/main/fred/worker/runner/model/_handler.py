from dataclasses import dataclass

from fred.settings import logger_manager
from fred.worker.interface import HandlerInterface
from fred.worker.runner.model.interface import ModelInterface

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=False)
class Handler(ModelInterface):
    classname: str
    classpath: str
    kwargs: dict

    def get_handler(self) -> HandlerInterface:
        return HandlerInterface.find_handler(
            handler_classname=self.classname,
            import_pattern=self.classpath,
            **self.kwargs,
        )

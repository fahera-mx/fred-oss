from dataclasses import dataclass

from fred.maturity import Maturity, MaturityLevel
from fred.worker.interface import HandlerInterface
from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


module_maturity = Maturity(
    level=MaturityLevel.TO_BE_DEPRECATED,
    reference=__name__,
    message=(
        "Runpod Helper implementation is soon to be deprecated! "
        "Please use the Fred-Worker interface instead (HandlerInterface)."
    )
)


@dataclass(frozen=True, slots=False)
class HandlerHelper(HandlerInterface):
    
    def __post_init__(self):
        super().__post_init__()
        logger.warning("Runpod Helper is soon to be deprecated! Please use Fred-Worker interface instead.")

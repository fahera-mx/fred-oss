import enum
from dataclasses import dataclass
from typing import Optional


from fred.settings import (
    logger_manager,
    get_environ_variable,
)


logger = logger_manager.get_logger(name=__name__)


class MaturityLevel(enum.Enum):
    ALPHA = (
        "Alpha Maturity Level"
        ": Initial development stage with potential instability and limited or unreliable features."
    )
    BETA = (
        "Beta Maturity Level"
        ": More stable than Alpha, with additional features and ongoing testing."
    )
    STABLE = (
        "Stable Maturity Level"
        ": Fully tested and mostly reliable, suitable for production use, but use at your own risk!"
    )
    TO_BE_DEPRECATED = (
        "To Be Deprecated Maturity Level"
        ": Functionality is planned to be removed in future releases. Consider alternatives."
    )
    DEPRECATED = (
        "Deprecated Maturity Level"
        ": Functionality is no longer supported and may be removed in future releases."
    )
    REMOVED = (
        "Removed Maturity Level"
        ": Functionality has been removed from the codebase and is no longer available."
    )

    def is_stable(self) -> bool:
        return self == MaturityLevel.STABLE
    
    def is_unstable(self) -> bool:
        return self in {MaturityLevel.ALPHA, MaturityLevel.BETA, MaturityLevel.TO_BE_DEPRECATED}
    
    def is_deprecated(self) -> bool:
        return self in {MaturityLevel.DEPRECATED, MaturityLevel.REMOVED}


@dataclass(frozen=True, slots=True)
class Maturity:
    level: MaturityLevel
    reference: Optional[str] = None
    message: Optional[str] = None


    def __post_init__(self):
        if not self.level.is_stable() and not self.quiet:
            logger.warning(
                "Functionality for {reference} is at {level} maturity level. {message}".format(
                    reference=self.reference or "undefined",
                    level=self.level.name,
                    message=self.message or ""
                )
            )

    @property
    def quiet(self) -> bool:
        return get_environ_variable(
            name="FRD_DISABLE_MATURITY_WARN",
            default="0",
        ).upper() in ["1", "Y", "T", "TRUE", "YES"]

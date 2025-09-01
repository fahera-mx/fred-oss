import time
import datetime as dt
from typing import Optional
from dataclasses import dataclass, field

from fred.settings import (
    get_environ_variable,
    logger_manager,
)

logger = logger_manager.get_logger(name=__name__)


@dataclass(slots=True, frozen=True)
class AbstractCLI:
    start_counter: float = field(default_factory=time.perf_counter)
    start_ts: str = field(default_factory=dt.datetime.utcnow().isoformat)

    def now(self, local: bool = False) -> str:
        return (dt.datetime.utcnow() if not local else dt.datetime.now()).isoformat()

    def environ(self, name: str) -> Optional[str]:
        return get_environ_variable(
            name=name,
            enforce=False,
        )

    def runtime(
            self,
            include_modules: bool = False,
        ) -> dict:
        from fred.utils.runtime import RuntimeInfo

        return RuntimeInfo.auto().to_dict(exclude_modules=not include_modules)

    def on_start(self):
        logger.debug("CLI Method not implemented: on_start")

    def on_finalize(self):
        logger.debug("CLI method not implemented: on_finalize")

    def __enter__(self) -> 'AbstractCLI':
        self.on_start()
        return self

    def __exit__(self, *args):
        self.on_finalize()
        end_counter = time.perf_counter()
        # TODO: Add warning logging if an error occurred
        logger.debug(f"Command Timestamp Start: {self.start_ts}")
        logger.debug(f"Command Timestamp Finalize: {self.now(local=False)}")
        logger.info(f"Command Duration: {end_counter - self.start_counter}")

    @classmethod
    def default_config(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def cli_exec(cls, *args, **kwargs):
        import fire

        with cls.default_config(*args, **kwargs) as cli:
            fire.Fire(cli)


class IntegrationExtCLI:
    pass
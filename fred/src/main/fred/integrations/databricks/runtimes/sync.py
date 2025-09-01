import os
import json
from dataclasses import dataclass
from typing import Union

from fred.integrations.databricks.runtime import DatabricksRuntimeCatalog
from fred.settings import logger_manager


logger = logger_manager.get_logger(name=__name__)

RUNTIME_DATATYPE = Union[DatabricksRuntimeCatalog, str]


@dataclass(frozen=True, slots=True)
class DatabricksRuntimeSyncHelper:
    output_path: str

    @classmethod
    def default(cls) -> 'DatabricksRuntimeSyncHelper':
        return cls(
            output_path=os.path.join(
                os.path.dirname(__file__),
                "runtimes",
            )
        )

    def get_payload(self, runtime: DatabricksRuntimeCatalog) -> list[dict]:
        import requests

        # Get the runtime content from the official documentation
        response = requests.get(runtime.url)
        if not response.ok:
            raise ValueError(f"Failed to fetch runtime information from {runtime.url}")
        content = response.text

        # Parse the content to extract relevant information
        # TODO: Implement the actual parsing logic
        raise NotImplementedError

    def sync(self, runtime: RUNTIME_DATATYPE):
        if isinstance(runtime, str):
            runtime = DatabricksRuntimeCatalog.from_string(runtime)
        logger.info(f"Syncing Databricks Runtime: {runtime.name}")
        payload = self.get_payload(runtime=runtime)
        output_filepath = os.path.join(
            self.output_path,
            f"{runtime.name.replace(' ', '')}.json",
        )
        with open(output_filepath, "w") as file:
            json.dump(payload, file, indent=4)

    def sync_all(self):
        for runtime in DatabricksRuntimeCatalog:
            self.sync(runtime=runtime)

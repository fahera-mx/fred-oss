import os
from enum import StrEnum, auto
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatabricksRuntime:
    python_version: str
    databricks_runtime: str
    libraries: list[dict]

    @classmethod
    def from_catalog(cls, catalog: 'DatabricksRuntimeCatalog') -> 'DatabricksRuntime':
        config = catalog.get_configuration()
        return cls(
            python_version=config.get("python_version", "3.12.3"),
            databricks_runtime=config.get("databricks_runtime", "16.4 LTS"),
            libraries=config.get("libraries", []),
        )


class DatabricksRuntimeCatalog(StrEnum):
    LTS_16_4 = auto()

    @property
    def key(self) -> str:
        runtime_type, runtime_num = self.name.split("_", 1)
        return f"{runtime_num.replace('_', '.')} {runtime_type}"

    @property
    def url(self) -> str:
        import posixpath
        return posixpath.join(
            "https://docs.databricks.com",
            "aws/en/release-notes/runtime",
            self.key.replace(" ", "").replace("_", "").lower(),
        )

    @classmethod
    def from_string(cls, name: str) -> 'DatabricksRuntimeCatalog':
        formatted_name = name.replace(" ", "").replace(".", "_").upper()
        return cls[formatted_name]

    def get_filepath(self) -> str:
        filename = f"{self.key.replace(' ', '').replace('.', '_')}.json"
        return os.path.join(
            os.path.dirname(__file__),
            "runtimes",
            filename,
        )
    
    def get_configuration(self) -> dict:
        import json

        with open(self.get_filepath(), "r") as file:
            return json.load(file)
        
    def get_runtime(self) -> DatabricksRuntime:
        return DatabricksRuntime.from_catalog(self)

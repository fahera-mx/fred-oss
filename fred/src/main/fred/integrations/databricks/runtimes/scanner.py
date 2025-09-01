from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatabricksRuntimeScanner:
    target_url: str

    @classmethod
    def default(cls) -> 'DatabricksRuntimeScanner':
        return cls(
            target_url="https://docs.databricks.com/aws/en/release-notes/runtime/"
        )

    def get_payload(self) -> list[dict]:
        # TODO: Extract the runtime table as a json/dict payload
        raise NotImplementedError

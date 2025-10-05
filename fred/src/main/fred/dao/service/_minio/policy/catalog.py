import enum
from typing import Optional

from fred.dao.service._minio.policy.loader import MinioPolicyLoader


class MinioPolicyCatalog(enum.Enum):
    BUCKET_PUBLIC_RO = MinioPolicyLoader(
        title="[Bucket Policy] Public Read-Only",
        filename="public_ro.json",
        requires=[
            "bucket_name",
        ],
    )
    BUCKET_PUBLIC_RW = MinioPolicyLoader(
        title="[Bucket Policy] Public Read-Write",
        filename="public_ro.json",
        requires=[
            "bucket_name",
        ],
    )

    def load(self, path: Optional[str] = None, **params) -> dict:
        return self.value.load(path=path, **params)
    
    def content(self, path: Optional[str] = None, **params) -> str:
        import json
        return json.dumps(self.load(path=path, **params))

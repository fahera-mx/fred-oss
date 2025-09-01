import datetime as dt
from typing import Optional


def datetime_now(tz: Optional[dt.tzinfo] = None) -> dt.datetime:
    return dt.datetime.now(tz=tz)

def datetime_utcnow() -> dt.datetime:
    return datetime_now(tz=dt.timezone.utc)

import time
from typing import TypeVar, Optional

from fred.future.settings import FRD_FUTURE_DEFAULT_EXPIRATION

A = TypeVar("A")


def pull_future_result(
        future_id: str,
        retry_delay: float = 0.2,
        retry_backoff_rate: float = 0.1,
        retry_delay_max: float = 15,
        timeout: float = FRD_FUTURE_DEFAULT_EXPIRATION,
    ) -> A:
    from fred.future.impl import FutureResult, FutureUndefinedInProgress, FutureUndefinedPending

    if timeout <= 0:
        raise ValueError(f"Pull operation for future_id '{future_id}' has timed out.")

    match FutureResult.from_backend(future_id=future_id):
        case None:
            raise ValueError(f"No future found with ID '{future_id}'")
        case FutureResult(value=value):
            return value.resolve()
        case FutureUndefinedPending() | FutureUndefinedInProgress():
            # If the future is not yet defined, wait for it to complete
            time.sleep(retry_delay)
            # Increase the delay for the next check to avoid busy waiting (exponential backoff) capped at delay_max
            return pull_future_result(
                future_id=future_id,
                retry_delay=min(retry_delay * (1 + retry_backoff_rate), retry_delay_max),
                retry_backoff_rate=retry_backoff_rate,
                retry_delay_max=retry_delay_max,
                # TODO: Consider using a more precise timeout mechanism based on elapsed time
                timeout=timeout - retry_delay,
            )
        case _:
            raise ValueError(f"Unknown future state for ID '{future_id}'")

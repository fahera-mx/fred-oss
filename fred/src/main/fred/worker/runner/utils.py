from typing import Optional

from fred.settings import get_environ_variable, logger_manager

logger = logger_manager.get_logger(name=__name__)


def get_queue_name_from_payload(
        payload: dict,
        search_keys: list[str],
        env_fallback: str,
        default: Optional[str] = None,
        keep: bool = False,
    ) -> str:
    for key in search_keys:
        if (queue_name := payload.get(key) if keep else payload.pop(key, None)):
            return queue_name
    return (
        queue_name
        or get_environ_variable(name=env_fallback, default=None)
        or (
            logger.warning(f"Redis queue not specified; defaulting to: '{default}'")
            or default
        )
    )

def get_request_queue_name_from_payload(
        payload: dict,
        keep: bool = False,
) -> Optional[str]:
    return get_queue_name_from_payload(
        payload=payload,
        search_keys=["redis_request_queue", "request_queue", "req_queue"],
        env_fallback="FRD_RUNNER_REQUEST_QUEUE",
        default="req:demo",
        keep=keep,
    )

def get_response_queue_name_from_payload(
        payload: dict,
        keep: bool = False,
) -> Optional[str]:
    return get_queue_name_from_payload(
        payload=payload,
        search_keys=["redis_response_queue", "response_queue", "res_queue"],
        env_fallback="FRD_RUNNER_RESPONSE_QUEUE",
        default=None,
        keep=keep,
    )

def get_redis_configs_from_payload(
        payload: dict,
        keep: bool = False,
    ) -> dict:
    for host_key in ["host", "redis_host"]:
        if (host := payload.get(host_key) if keep else payload.pop(host_key, None)):
            break
    for port_key in ["port", "redis_port"]:
        if (port := payload.get(port_key) if keep else payload.pop(port_key, None)):
            break
    for password_key in ["password", "redis_password"]:
        if (password := payload.get(password_key) if keep else payload.pop(password_key, None)):
            break
    for db_key in ["db", "redis_db"]:
        if (db := payload.get(db_key) if keep else payload.pop(db_key, None)):
            break
    return {
        "host": host or get_environ_variable(name="REDIS_HOST", default="localhost"),
        "port": int(port or get_environ_variable(name="REDIS_PORT", default=6379)),
        "password": password or get_environ_variable(name="REDIS_PASSWORD", default=None),
        "db": int(db or get_environ_variable(name="REDIS_DB", default=0)),
        "decode_responses": True,
        **(payload.get("redis_configs", {}) if keep else payload.pop("redis_configs", {})),
    }

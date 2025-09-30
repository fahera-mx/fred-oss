from fred.settings import get_environ_variable


def get_redis_configs_from_payload(
        payload: dict,
        keep: bool = False,
    ) -> dict:
    """Extract Redis configuration from the given payload dictionary.
    This function looks for common Redis configuration keys in the payload
    dictionary. If a key is not found, it falls back to environment variables.
    Args:
        payload (dict): The dictionary from which to extract Redis configuration.
        keep (bool): If True, the original keys are retained in the payload. If False, they are removed.
    Returns:
        dict: A dictionary containing Redis configuration parameters.
    """
    host = port = password = db = None
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
        "host": host or get_environ_variable(name="REDIS_HOST", default=None) or "localhost",
        "port": int(port or get_environ_variable(name="REDIS_PORT", default=None) or 6379),
        "password": password or get_environ_variable(name="REDIS_PASSWORD", default=None),
        "db": int(db or get_environ_variable(name="REDIS_DB", default=None) or 0),
        "decode_responses": True,
        **(payload.get("redis_configs", {}) if keep else payload.pop("redis_configs", {})),
    }

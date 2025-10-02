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


def get_minio_from_payload(
        payload: dict,
        keep: bool = False,
):
    """Extract MinIO configuration from the given payload dictionary.
    This function looks for common MinIO configuration keys in the payload
    dictionary. If a key is not found, it falls back to environment variables.
    Args:
        payload (dict): The dictionary from which to extract MinIO configuration.
        keep (bool): If True, the original keys are retained in the payload. If False, they are removed.
    Returns:
        dict: A dictionary containing MinIO configuration parameters.
    """
    endpoint = access_key = secret_key = region = secure = None
    for endpoint_key in ["endpoint", "minio_endpoint"]:
        if (endpoint := payload.get(endpoint_key) if keep else payload.pop(endpoint_key, None)):
            break
    for access_key_key in ["access_key", "minio_access_key"]:
        if (access_key := payload.get(access_key_key) if keep else payload.pop(access_key_key, None)):
            break
    for secret_key_key in ["secret_key", "minio_secret_key"]:
        if (secret_key := payload.get(secret_key_key) if keep else payload.pop(secret_key_key, None)):
            break
    for secure_key in ["secure", "minio_secure"]:
        if (secure := payload.get(secure_key) if keep else payload.pop(secure_key, None)):
            break
    for region_key in ["region", "minio_region"]:
        if (region := payload.get(region_key) if keep else payload.pop(region_key, None)):
            break
    return {
        "endpoint": endpoint or get_environ_variable(name="MINIO_ENDPOINT", default=None) or "localhost:9000",
        "access_key": access_key or get_environ_variable(name="MINIO_ACCESS_KEY", default=None) or "minioadmin",
        "secret_key": secret_key or get_environ_variable(name="MINIO_SECRET_KEY", default=None) or "minioadmin",
        "secure": bool(secure or get_environ_variable(name="MINIO_SECURE", default=None) or True),  # Default to True
        "region": region or get_environ_variable(name="MINIO_REGION", default=None) or "us-east-1",
        **(payload.get("minio_configs", {}) if keep else payload.pop("minio_configs", {})),
    }

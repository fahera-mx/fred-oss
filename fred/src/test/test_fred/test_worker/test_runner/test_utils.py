from fred.worker.runner.utils import (
    get_queue_name_from_payload,
    get_request_queue_name_from_payload,
    get_response_queue_name_from_payload,
    get_redis_configs_from_payload,
)


def test_get_queue_name_from_payload():
    payload = {
        "key1": "value1",
        "key2": "value2",
    }
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key1", "key2"],
        env_fallback="NON_EXISTENT_ENV",
        default="default_value",
        keep=False,
    ) == "value1"
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key3", "key2"],
        env_fallback="NON_EXISTENT_ENV",
        default="default_value",
        keep=False,
    ) == "value2"
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key3", "key4"],
        env_fallback="NON_EXISTENT_ENV",
        default="default_value",
        keep=False,
    ) == "default_value"
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key3", "key4"],
        env_fallback="NON_EXISTENT_ENV",
        default=None,
        keep=False,
    ) is None
    # Test with 'keep=True'
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key1", "key2"],
        env_fallback="NON_EXISTENT_ENV",
        default="default_value",
        keep=True,
    ) == "value1"
    assert "key1" in payload  # Ensure key is kept
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key3", "key2"],
        env_fallback="NON_EXISTENT_ENV",
        default="default_value",
        keep=True,
    ) == "value2"
    assert "key2" in payload  # Ensure key is kept
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key3", "key4"],
        env_fallback="NON_EXISTENT_ENV",
        default="default_value",
        keep=True,
    ) == "default_value"
    assert get_queue_name_from_payload(
        payload=payload.copy(),
        search_keys=["key3", "key4"],
        env_fallback="NON_EXISTENT_ENV",
        default=None,
        keep=True,
    ) is None # Ensure None is returned
    assert "key1" in payload and "key2" in payload  # Ensure original keys are kept

def test_get_request_queue_name_from_payload():
    payload = {
        "redis_request_queue": "redis_req_queue",
        "request_queue": "req_queue",
        "req_queue": "short_req_queue",
    }
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=False) == "redis_req_queue"
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=True) == "redis_req_queue"
    payload.pop("redis_request_queue")
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=False) == "req_queue"
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=True) == "req_queue"
    payload.pop("request_queue")
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=False) == "short_req_queue"
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=True) == "short_req_queue"
    payload.pop("req_queue")
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=False) == "req:demo"
    assert get_request_queue_name_from_payload(payload=payload.copy(), keep=True) == "req:demo"

def test_get_response_queue_name_from_payload():
    payload = {
        "redis_response_queue": "redis_res_queue",
        "response_queue": "res_queue",
        "res_queue": "short_res_queue",
    }
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=False) == "redis_res_queue"
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=True) == "redis_res_queue"
    payload.pop("redis_response_queue")
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=False) == "res_queue"
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=True) == "res_queue"
    payload.pop("response_queue")
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=False) == "short_res_queue"
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=True) == "short_res_queue"
    payload.pop("res_queue")
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=False) is None
    assert get_response_queue_name_from_payload(payload=payload.copy(), keep=True) is None
    assert "redis_response_queue" not in payload
    assert "response_queue" not in payload
    assert "res_queue" not in payload
    assert payload == {}  # Ensure original payload is empty after pops

def test_get_redis_configs_from_payload():
    payload = {
        "host": "localhost",
        "port": 6379,
        "password": "secret",
        "db": 0,
    }
    configs = get_redis_configs_from_payload(payload=payload, keep=False)
    assert configs == {
        "host": "localhost",
        "port": 6379,
        "password": "secret",
        "db": 0,
        "decode_responses": True,
    }
    assert "host" not in payload
    assert "port" not in payload
    assert "password" not in payload
    assert "db" not in payload
    payload = {
        "host": "localhost",
        "port": 6379,
        "password": "secret",
        "db": 0,
    }
    configs = get_redis_configs_from_payload(payload=payload, keep=True)
    assert configs == {
        "host": "localhost",
        "port": 6379,
        "password": "secret",
        "db": 0,
        "decode_responses": True,
    }
    assert "host" in payload
    assert "port" in payload
    assert "password" in payload
    assert "db" in payload

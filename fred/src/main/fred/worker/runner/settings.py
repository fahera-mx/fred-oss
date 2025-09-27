from fred.settings import get_environ_variable


FRD_RUNNER_BACKEND = get_environ_variable(
    name="FRD_RUNNER_BACKEND",
    default="STDLIB",
).upper()

FRD_RUNNER_REQUEST_QUEUE = get_environ_variable(
    name="FRD_RUNNER_REQUEST_QUEUE",
    default=None,
)

FRD_RUNNER_RESPONSE_QUEUE = get_environ_variable(
    name="FRD_RUNNER_RESPONSE_QUEUE",
    default=None,
)

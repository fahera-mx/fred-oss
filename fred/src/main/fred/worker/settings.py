from fred.settings import get_environ_variable


FRD_WORKER_DEFAULT_BROADCAST = bool(int(get_environ_variable(
    name="FRD_WORKER_BROADCAST_DEFAULT",
    default="0",
)) or 0)

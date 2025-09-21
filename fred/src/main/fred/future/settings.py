from fred.settings import get_environ_variable


FRD_FUTURE_BACKEND = get_environ_variable(
    "FRD_FUTURE_BACKEND",
    default="STDLIB",
)

FRD_FUTURE_DEFAULT_EXPIRATION = int(get_environ_variable(
    "FRD_FUTURE_DEFAULT_EXPIRATION",
    default="3600",  # 1 hour
))

# TODO: This is currently not used, but reserved for future use...
FRD_FUTURE_DEFAULT_TIMEOUT = int(get_environ_variable(
    "FRD_FUTURE_DEFAULT_TIMEOUT",
    default="900",  # 15 minutes
))

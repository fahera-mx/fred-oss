"""
[Fred-REST] Fred's Simple Extensible REST-API Server
========================================================
This module provides a simple and extensible REST-API server implementation using FastAPI.
It includes configurations for authentication, router management, and server startup.
"""
from fred.maturity import Maturity, MaturityLevel


module_maturity = Maturity(
    level=MaturityLevel.ALPHA,
    reference=__name__,
    message=(
        "Fred-REST implementation is in early development "
        "and therefore currently with incomplete and unstable features."
    )
)

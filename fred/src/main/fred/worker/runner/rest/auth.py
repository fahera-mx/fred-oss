from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from fred.worker.runner.rest.settings import FRD_RESTAPI_TOKEN

async def verify_key(
        api_key_header: str = Security(
            APIKeyHeader(
                name="X-API-Key",
                auto_error=False
            )
        ),
):
    """
    Verify the provided API key against the expected token.
    Raises an HTTPException if the key is invalid or missing.
    """
    if api_key_header != FRD_RESTAPI_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )

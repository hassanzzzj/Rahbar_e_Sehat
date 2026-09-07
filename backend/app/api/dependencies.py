"""
FastAPI dependency injection for authentication and rate limiting.
Provides reusable guards that can be applied to route handlers.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


async def verify_api_key(authorization: Annotated[str | None, Header()] = None) -> str:
    """
    Verify API key from Authorization header.
    Returns the validated API key or raises 401.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
        )

    token = authorization[7:]

    # TODO: Validate token against database or JWT
    # For now, accept any non-empty token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return token


async def verify_admin_role(
    api_key: Annotated[str, Depends(verify_api_key)]
) -> str:
    """
    Verify that the authenticated user has admin role.
    Used to protect admin endpoints.
    """
    # TODO: Check role from token claims or database
    # For now, placeholder implementation
    return api_key

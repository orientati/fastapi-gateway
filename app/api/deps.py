from typing import Annotated, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services import auth
from app.services.http_client import OrientatiException, HttpCodes
from app.core.logging import get_logger

logger = get_logger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

async def validate_token(token: Annotated[str, Depends(reusable_oauth2)]) -> Dict[str, Any]:
    """
    Centralized token validation dependency.
    Verifies the token with the auth service and handles errors securely.
    Returns the token payload if valid.
    """
    try:
        payload = await auth.verify_token(token)
        
        # Additional Security Checks can be added here
        # e.g., checking specific claims, although verify_token should handle most.
        if not payload or not payload.get("verified"):
             logger.warning(f"Token validation failed: payload={payload}")
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload

    except OrientatiException as e:
        # Log the specific underlying error for internal auditing but return standard 401/403
        logger.warning(f"Token verification exception: {str(e)}")
        
        # If the service explicitly returned 401 or 403, we respect that.
        # Otherwise, if it was a connection error or 500 from auth service, 
        # we might want to return 401 (fail closed) or 503 (service unavailable).
        # For security (fail closed), 401 is generally safer to avoid revealing infra issues,
        # but 503 is more semantically correct for downstream failures.
        # Given "extreme security", we default to 401 for any verification ambiguity 
        # to prevent bypassing auth due to soft errors, unless it's clearly an upstream availability issue.
        
        if e.status_code in [401, 403]:
             raise HTTPException(
                status_code=e.status_code,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fallback for other errors (e.g. 500 from token service) -> Treat as 401 to be safe? 
        # Or 502/503? 
        # 'verify_token' in auth.py handles 500 from upstream as InvalidTokenException (401).
        # So we likely just re-raise as HTTPException if it hasn't been mapped yet.
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Type alias for easier usage in routes
CurrentTokenPayload = Annotated[Dict[str, Any], Depends(validate_token)]

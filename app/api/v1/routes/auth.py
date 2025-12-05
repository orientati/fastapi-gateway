from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.core.logging import get_logger
from app.schemas.auth import UserLogin, TokenResponse, TokenRequest, UserRegistration, UserLogout
from app.services import auth
from app.services.http_client import OrientatiException

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_json: UserLogin | None = None
):
    try:
        if form_data:
            # Swagger UI invia username e password come form data
            user = UserLogin(email=form_data.username, password=form_data.password)
        elif user_json:
            user = user_json
        else:
             raise HTTPException(status_code=400, detail="Missing credentials")
             
        return await auth.login(user)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/refresh", response_model=TokenResponse)
async def post_refresh_token(refresh_token: TokenRequest):
    try:
        return await auth.refresh_token(refresh_token)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/logout", response_model=UserLogout)
async def logout(access_token: TokenRequest):
    try:
        return await auth.logout(access_token)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegistration):
    try:
        return await auth.register(user)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )

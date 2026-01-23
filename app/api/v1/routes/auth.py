from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.limiter import limiter
from app.db.session import get_db
from app.schemas.auth import UserLogin, TokenResponse, TokenRequest, UserRegistration, UserLogout
from app.db.session import get_db
from app.services import auth
from app.services.http_client import OrientatiException

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_json: Optional[UserLogin] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        if form_data:
            # Swagger UI invia username e password come form data
            try:
                user = UserLogin(email=form_data.username, password=form_data.password)
            except ValidationError as e:
                # Se la validazione fallisce, solleva un'eccezione 422
                raise HTTPException(status_code=422, detail=e.errors())
        elif user_json:
            user = user_json
        else:
             raise HTTPException(status_code=400, detail="Missing credentials")
             
        return await auth.login(user, db)
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
@limiter.limit("20/minute")
async def post_refresh_token(request: Request, refresh_token: TokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth.refresh_token(refresh_token, db)
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
@limiter.limit("20/minute")
async def logout(request: Request, access_token: TokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth.logout(access_token, db)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/register", status_code=202)
@limiter.limit("5/minute")
async def register(request: Request, user: UserRegistration, db: AsyncSession = Depends(get_db)):
    try:
        await auth.register(user, db)
        return {"message": "Registration successful. Please check your email to verify your account."}

    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )

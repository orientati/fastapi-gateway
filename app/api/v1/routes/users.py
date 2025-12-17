from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from app.api.deps import reusable_oauth2

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

from app.core.logging import get_logger
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse, UpdateUserRequest, DeleteUserResponse
from app.services import users, auth
from app.services.http_client import OrientatiException, HttpCodes

logger = get_logger(__name__)
router = APIRouter()


@router.post("/change_password", response_model=ChangePasswordResponse)
async def change_password(passwords: ChangePasswordRequest, token: str = Depends(reusable_oauth2)):
    try:
        payload = await auth.verify_token(token)
        changed = await users.change_password(passwords, payload["user_id"])
        if changed:
            return ChangePasswordResponse()
        else:
            raise OrientatiException(
                status_code=HttpCodes.BAD_REQUEST,
                message="Password change failed",
                details={"message": "Password change failed due to unknown reasons"},
                url="users/change_password"
            )
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.patch("/", response_model=UpdateUserRequest)
async def update_user_self(new_data: UpdateUserRequest, token: str = Depends(reusable_oauth2)):
    try:
        payload = await auth.verify_token(token)
        return await users.update_user(payload["user_id"], new_data)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.patch("/{user_id}", response_model=UpdateUserRequest)
async def update_user(user_id: int, new_data: UpdateUserRequest, token: str = Depends(reusable_oauth2)):
    try:
        # TODO: verificare che l'utente abbia i permessi per modificare un altro utente
        payload = await auth.verify_token(token)
        if payload["user_id"] != user_id:
             raise OrientatiException(
                status_code=HttpCodes.FORBIDDEN,
                message="Forbidden",
                details={"message": "You are not allowed to update this user"},
                url=f"users/{user_id}"
            )
        return await users.update_user(user_id, new_data)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.delete("/{user_id}", response_model=DeleteUserResponse)
async def delete_user(user_id: int, token: str = Depends(reusable_oauth2)):
    try:
        # TODO: verificare che l'utente abbia i permessi per eliminare un altro utente
        payload = await auth.verify_token(token)
        if payload["user_id"] != user_id:
             raise OrientatiException(
                status_code=HttpCodes.FORBIDDEN,
                message="Forbidden",
                details={"message": "You are not allowed to delete this user"},
                url=f"users/{user_id}"
            )
        return await users.delete_user(user_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )



# funzione che restituisce se l'utente che la sta chiamando ha la email verificata
@router.get("/email_status")
async def email_status(token: str = Depends(reusable_oauth2), db: AsyncSession = Depends(get_db)):
    try:
        payload = await auth.verify_token(token) #TODO: verificare il token
        is_verified = await users.get_email_status_from_token(token, db)

        return JSONResponse(
            status_code=HttpCodes.OK,
            content={
                "status": "verified" if is_verified else "not verified",
            }
        )
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.get("/verify_email")
async def verify_email(token: str):
    try:
        verified = await users.verify_email(token)
        if verified:
            return JSONResponse(
                status_code=HttpCodes.OK,
                content={
                    "message": "Email verified successfully"
                }
            )
        else:
            raise OrientatiException(
                status_code=HttpCodes.BAD_REQUEST,
                message="Email verification failed",
                details={"message": "Email verification failed due to unknown reasons"},
                url="users/verify_email"
            )
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )

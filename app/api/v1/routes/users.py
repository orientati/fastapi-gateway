from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse, UpdateUserRequest, DeleteUserResponse
from app.services import users, auth
from app.services.http_client import OrientatiException, HttpCodes

logger = get_logger(__name__)
router = APIRouter()


@router.post("/change_password", response_model=ChangePasswordResponse)
async def change_password(passwords: ChangePasswordRequest, request: Request):
    try:
        token = request.headers.get("Authorization")
        if not token:
            raise OrientatiException(
                status_code=HttpCodes.UNAUTHORIZED,
                message="Missing Authorization header",
                details={"message": "Unauthorized"},
                url="users/change_password"
            )
        token = token.replace("Bearer ", "").strip()
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
async def update_user_self(new_data: UpdateUserRequest, request: Request):
    try:
        token = request.headers.get("Authorization")
        if not token:
            raise OrientatiException(
                status_code=HttpCodes.UNAUTHORIZED,
                message="Missing Authorization header",
                details={"message": "Unauthorized"},
                url="users/update_user_self"
            )
        token = token.replace("Bearer ", "").strip()
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
async def update_user(user_id: int, new_data: UpdateUserRequest, request: Request):
    try:
        # TODO: verificare che l'utente abbia i permessi per modificare un altro utente
        token = request.headers.get("Authorization")
        if not token:
            raise OrientatiException(
                status_code=HttpCodes.UNAUTHORIZED,
                message="Missing Authorization header",
                details={"message": "Unauthorized"},
                url="users/update_user"
            )
        token = token.replace("Bearer ", "").strip()
        await auth.verify_token(token)
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
async def delete_user(user_id: int, request: Request):
    try:
        # TODO: verificare che l'utente abbia i permessi per eliminare un altro utente
        token = request.headers.get("Authorization")
        if not token:
            raise OrientatiException(
                status_code=HttpCodes.UNAUTHORIZED,
                message="Missing Authorization header",
                details={"message": "Unauthorized"},
                url="users/delete_user"
            )
        token = token.replace("Bearer ", "").strip()
        await auth.verify_token(token)
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
async def email_status(request: Request):
    try:
        token = request.headers.get("Authorization")
        if not token:
            raise OrientatiException(status_code=HttpCodes.UNAUTHORIZED, message="Missing Authorization header")
        status = users.get_email_status_from_token(token)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "verified" if status else "not verified",
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

# @router.get("/testrabbit")
# async def test_rabbitmq(request: Request):
#    broker_instance = broker.AsyncBrokerSingleton()
#    await broker_instance.connect()
#    await broker_instance.publish_message("users", "ADD", {})
#    await broker_instance.publish_message("banana", "ADD", {})
#    return {"message": "Message sent to RabbitMQ"}

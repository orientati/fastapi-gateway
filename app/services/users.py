import json
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.session import Session
from app.models.user import User
from app.schemas.users import ChangePasswordRequest, UpdateUserRequest, UpdateUserResponse, \
    DeleteUserResponse
from app.services.auth import get_session_id_from_token
from app.services.http_client import OrientatiException, HttpMethod, HttpUrl, HttpParams, send_request

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

RABBIT_DELETE_TYPE = "DELETE"
RABBIT_UPDATE_TYPE = "UPDATE"
RABBIT_CREATE_TYPE = "CREATE"


async def change_password(passwords: ChangePasswordRequest, user_id: int) -> bool:
    try:
        old_password_hashed = pwd_context.hash(passwords.old_password)
        new_password_hashed = pwd_context.hash(passwords.new_password)
        params = HttpParams()
        params.add_param("user_id", user_id)
        params.add_param("old_password", old_password_hashed)
        params.add_param("new_password", new_password_hashed)
        response, status_code = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.USERS_SERVICE,
            endpoint="/users/change_password",
            _params=params
        )
        if status_code >= 400:
            raise OrientatiException(message=response.get("message", "Error changing password"),
                                     status_code=status_code, details={"message": "Error changing password"})
        return True
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/change_password")


async def update_user(user_id: int, new_data: UpdateUserRequest) -> UpdateUserResponse:
    try:
        params = HttpParams()
        # email rimosso
        params.add_param("name", new_data.name) if new_data.name else None
        params.add_param("surname", new_data.surname) if new_data.surname else None
        response, status_code = await send_request(
            method=HttpMethod.PATCH,
            url=HttpUrl.USERS_SERVICE,
            endpoint=f"/users/{user_id}",
            _params=params
        )
        if status_code >= 400:
            raise OrientatiException(message=response.get("message", "Errore durante l'aggiornamento dell'utente"), status_code=status_code,
                                     details={"message": "Errore durante l'aggiornamento dell'utente"})
        return UpdateUserResponse()
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/update_user")


async def delete_user(user_id: int) -> DeleteUserResponse:
    try:
        response, status_code = await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.USERS_SERVICE,
            endpoint=f"/users/{user_id}"
        )
        if status_code >= 400:
            raise OrientatiException(message=response.get("message", "Error deleting user"), status_code=status_code,
                                     details={"message": "Error deleting user"})
        return DeleteUserResponse()
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/delete_user")


async def update_from_rabbitMQ(message):
    async with message.process():
        try:
            async with AsyncSessionLocal() as db:
                response = message.body.decode()
                json_response = json.loads(response)
                msg_type = json_response["type"]
                data = json_response["data"]

                logger.info(f"Received message from RabbitMQ: {msg_type} - {data}")

                stmt = select(User).where(User.id == data["id"])
                result = await db.execute(stmt)
                user = result.scalars().first()

                if msg_type == RABBIT_UPDATE_TYPE:
                    if user is None:
                        # Se l'utente non esiste, lo creiamo (potrebbe essere arrivato prima l'update del create?)
                        # O semplicemente sincronizziamo
                        user = User(
                            id=data["id"],
                            email=data["email"],
                            # email_verified logic might vary, assuming field exists
                            # email_verified=data.get("email_verified", False), 
                            hashed_password=data["hashed_password"],
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"])
                        )
                        # Check optional fields if user model supports them and they are in data
                        if "email_verified" in data:
                             user.email_verified = data["email_verified"]
                        
                        if "name" in data: user.name = data["name"]
                        if "surname" in data: user.surname = data["surname"]

                        db.add(user)
                        await db.commit()
                        logger.warning(f"User with id {data['id']} not found during update. Created new user.")
                        return

                    user.email = data["email"]
                    if "email_verified" in data:
                         user.email_verified = data["email_verified"]
                    if "name" in data: user.name = data["name"]
                    if "surname" in data: user.surname = data["surname"]
                    
                    user.hashed_password = data["hashed_password"]
                    user.updated_at = datetime.fromisoformat(data["updated_at"])
                    await db.commit()

                elif msg_type == RABBIT_DELETE_TYPE:
                    if user:
                        await db.delete(user)
                        await db.commit()
                    else:
                        logger.error(f"User with id {data['id']} not found during delete.")

                elif msg_type == RABBIT_CREATE_TYPE:
                    # Usually handled by auth/register logic or sync logic
                    pass
                else:
                    logger.error(f"Unsupported message type: {msg_type}")
        except Exception as e:
            raise OrientatiException(exc=e, url="users/update_from_rabbitMQ")


async def get_email_status_from_token(token: str, db: AsyncSession):
    try:
        session_id = await get_session_id_from_token(token)
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            raise OrientatiException(
                status_code=404,
                message="Not Found",
                details={"message": "Session not found"},
                url="users/get_email_status_from_token"
            )
        
        stmt_user = select(User).where(User.id == session.user_id)
        res_user = await db.execute(stmt_user)
        user = res_user.scalars().first()

        if not user:
            raise OrientatiException(
                status_code=404,
                message="Not Found",
                details={"message": "User not found"},
                url="users/get_email_status_from_token"
            )
        return user.email_verified
    except Exception as e:
        raise e


async def verify_email(token):
    try:
        params = HttpParams()
        params.add_param("token", token)
        response, status_code = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.USERS_SERVICE,
            endpoint=f"/users/verify_email",
            _params=params
        )
        if status_code == 204:
            return True
        else:
            return False
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/verify_email")

from datetime import datetime, timedelta

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.accessToken import AccessToken
from app.models.refreshToken import RefreshToken
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import UserLogin, TokenResponse, TokenRequest, UserRegistration, UserLogout
from app.services.http_client import OrientatiException, HttpMethod, HttpUrl, HttpParams, send_request, HttpCodes

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto", argon2__rounds=1, argon2__memory_cost=64)
# Hash fittizio per mitigazione attacchi temporali
DUMMY_PWD_HASH = pwd_context.hash("dummy_password_for_safety")


# Custom exception per invalid credentials
class InvalidCredentialsException(OrientatiException):
    def __init__(self, message: str = "Credenziali non valide"):
        self.message = "Unauthorized"
        self.status_code = 401
        self.url = "/login"
        self.details = {"message": message}

    pass


# Custom exception per invalid session
class InvalidSessionException(OrientatiException):
    def __init__(self, message: str):
        self.message = "Forbidden"
        self.status_code = 403
        self.url = "/logout"
        self.details = {"message": message}

    pass


class InvalidTokenErrorType:
    INVALID_TOKEN = 1
    TOKEN_NOT_FOUND = 2
    INACTIVE_SESSION = 3
    BLOCKED_SESSION = 4
    EXPIRED_SESSION = 5


# Custom exception per invalid token
class InvalidTokenException(OrientatiException):
    def __init__(self, message: str, error_type: int):
        self.message = "Unauthorized"
        self.status_code = 401
        self.url = "/token/verify"
        self.details = {"message": message, "error_type": error_type}

    pass


async def create_access_token(data: dict, expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES) -> dict:
    try:
        params = HttpParams(data)
        if expire_minutes:
            params.add_param("expires_in", expire_minutes)

        json_data, status_code = await send_request(
            url=HttpUrl.TOKEN_SERVICE,
            method=HttpMethod.POST,
            endpoint="/token/create",
            _params=params
        )
        if status_code >= 400:
            message = json_data.get("message", "Error creating access token") if json_data else "Error creating access token"
            raise OrientatiException(message=message, status_code=status_code, details={"message": message})
        return json_data
    except OrientatiException as e:
        raise e


async def create_refresh_token(data: dict, expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS) -> dict:
    try:
        params = HttpParams(data)
        if expire_days:
            params.add_param("expires_in", expire_days * 24 * 60)  # Converti giorni in minuti

        json_data, status_code = await send_request(
            url=HttpUrl.TOKEN_SERVICE,
            method=HttpMethod.POST,
            endpoint="/token/create",
            _params=params
        )
        if status_code >= 400:
            message = json_data.get("message", "Error creating refresh token") if json_data else "Error creating refresh token"
            raise OrientatiException(message=message, status_code=status_code, details={"message": message})
        return json_data
    except OrientatiException as e:
        raise e


async def create_new_user(data: dict) -> dict:
    try:
        params = HttpParams(data)
        json_data, status_code = await send_request(
            url=HttpUrl.USERS_SERVICE,
            method=HttpMethod.POST,
            endpoint="/users/",
            _params=params
        )
        if status_code >= 400:
            message = json_data.get("message", "Error creating user") if json_data else "Error creating user"
            raise OrientatiException(message=message, status_code=status_code, details={"message": message})
        return json_data
    except OrientatiException as e:
        raise e


async def verify_token(token: str) -> dict:
    try:
        params = HttpParams({"token": token})
        json_data, status_code = await send_request(
            url=HttpUrl.TOKEN_SERVICE,
            method=HttpMethod.POST,
            endpoint="/token/verify",
            _params=params
        )
        if status_code >= 400:
            if status_code == 500:
                logger.warning(f"Token service returned 500 for token verification. Treating as invalid token. Response: {json_data}")
                raise InvalidTokenException("Token verification failed (upstream error)", InvalidTokenErrorType.INVALID_TOKEN)
            
            message = json_data.get("message", "Error verifying token") if json_data else "Error verifying token"
            raise OrientatiException(message=message, status_code=status_code, details={"message": message})
        return json_data
    except OrientatiException as e:
        raise e


def verify_password(plain_password: str, hashed_password: str):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (UnknownHashError, ValueError):
        return False


async def create_user_session_and_tokens(user: User, db: AsyncSession) -> TokenResponse:
    db_session = Session(
        user_id=user.id,
        expires_at=datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    access_token_response = await create_access_token(
        data={"user_id": user.id, "session_id": db_session.id}
    )
    access_token = access_token_response["token"]

    refresh_token_response = await create_refresh_token(
        data={"user_id": user.id, "session_id": db_session.id}
    )
    refresh_token = refresh_token_response["token"]

    db_access_token = AccessToken(
        session_id=db_session.id,
        token=access_token
    )
    db.add(db_access_token)
    await db.commit()
    await db.refresh(db_access_token)

    db_refresh_token = RefreshToken(
        session_id=db_session.id,
        token=refresh_token,
        accessToken_id=db_access_token.id
    )
    db.add(db_refresh_token)
    await db.commit()
    await db.refresh(db_refresh_token)

    return TokenResponse(status_code=HttpCodes.CREATED.value, access_token=access_token, refresh_token=refresh_token)


async def login(user_login: UserLogin, db: AsyncSession) -> TokenResponse:
    try:
        stmt = select(User).where(User.email == user_login.email)
        result = await db.execute(stmt)
        user = result.scalars().first()

        password_valid = False
        if user:
            password_valid = verify_password(user_login.password, user.hashed_password)
        else:
            verify_password(user_login.password, DUMMY_PWD_HASH)
            password_valid = False

        if not user or not password_valid:
            raise InvalidCredentialsException()

        if not user.email_verified:
             raise InvalidCredentialsException()

        return await create_user_session_and_tokens(user, db)
    except (InvalidCredentialsException, OrientatiException) as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/login", exc=e)


async def refresh_token(refresh_token: TokenRequest, db: AsyncSession) -> TokenResponse:
    try:
        payload = await verify_token(refresh_token.token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid refresh token", InvalidTokenErrorType.INVALID_TOKEN)

        stmt = select(RefreshToken).join(AccessToken).where(RefreshToken.token == refresh_token.token)
        result = await db.execute(stmt)
        db_old_refresh_token = result.scalars().first()

        if not db_old_refresh_token:
            raise InvalidTokenException("Refresh token not found", InvalidTokenErrorType.TOKEN_NOT_FOUND)

        stmt_session = select(Session).where(Session.id == db_old_refresh_token.session_id)
        res_session = await db.execute(stmt_session)
        session = res_session.scalars().first()

        if not session or not session.is_active:
            raise InvalidTokenException("Session is inactive or does not exist", InvalidTokenErrorType.INACTIVE_SESSION)
        if session.is_blocked:
            raise InvalidTokenException("Session is blocked", InvalidTokenErrorType.BLOCKED_SESSION)
        if session.expires_at < datetime.now():
            raise InvalidTokenException("Session expired", InvalidTokenErrorType.EXPIRED_SESSION)

        if db_old_refresh_token.is_expired:
            session.is_active = False
            session.is_blocked = True
            await db.commit()
            await db.refresh(session)
            
            await db.execute(update(AccessToken).where(AccessToken.session_id == session.id).values(is_expired=True))
            await db.execute(update(RefreshToken).where(RefreshToken.session_id == session.id).values(is_expired=True))
            await db.commit()

            raise InvalidTokenException("Refresh token expired, Session blocked", InvalidTokenErrorType.EXPIRED_SESSION)

        access_token_response = await create_access_token(
            {"user_id": payload["user_id"], "session_id": session.id})
        refresh_token_response = await create_refresh_token(
            {"user_id": payload["user_id"], "session_id": session.id},
            expire_days=(
                    session.expires_at - datetime.now()).days)
        access_token = access_token_response["token"]
        refresh_token_new = refresh_token_response["token"]
        
        db_old_refresh_token.is_expired = True
        await db.commit()
        await db.refresh(db_old_refresh_token)
        
        # AccessToken relation loading might be an issue if not lazy loaded or eager loaded. 
        # But we can update via query if we don't have the object loaded
        # db_old_refresh_token.accessToken.is_expired = True 
        # Better use update query or ensure relationship is loaded
        # Assuming eager load or just update by ID if we have it
        if db_old_refresh_token.accessToken:
             db_old_refresh_token.accessToken.is_expired = True
             await db.commit() # Save changes
        else:
             # Fallback update query
             # Need the access token ID linked to this refresh token
             pass 

        db_access_token = AccessToken(
            session_id=session.id,
            token=access_token,
        )
        db.add(db_access_token)
        await db.commit()
        await db.refresh(db_access_token)
        
        db_refresh_token = RefreshToken(
            session_id=session.id,
            token=refresh_token_new,
            accessToken_id=db_access_token.id
        )
        db.add(db_refresh_token)
        await db.commit()
        await db.refresh(db_refresh_token)

        return TokenResponse(status_code=HttpCodes.CREATED.value, access_token=access_token,
                             refresh_token=refresh_token_new)
    except (InvalidTokenException, OrientatiException) as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/refresh", exc=e)


async def logout(access_token: TokenRequest, db: AsyncSession) -> UserLogout:
    try:
        payload = await verify_token(access_token.token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid access token", InvalidTokenErrorType.INVALID_TOKEN)

        if payload["expired"]:
            raise InvalidTokenException("Access token expired", InvalidTokenErrorType.EXPIRED_SESSION)

        stmt = select(Session).where(Session.id == payload["session_id"])
        result = await db.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            raise InvalidSessionException("Session does not exist")

        session.is_active = False
        await db.commit()
        await db.refresh(session)

        # Segno tutti i token associati alla sessione come scaduti
        await db.execute(update(AccessToken).where(AccessToken.session_id == session.id).values(is_expired=True))
        await db.execute(update(RefreshToken).where(RefreshToken.session_id == session.id).values(is_expired=True))
        await db.commit()

        return UserLogout()
    except (InvalidTokenException, InvalidSessionException, OrientatiException) as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/logout", exc=e)


async def register(user: UserRegistration, db: AsyncSession) -> None:
    try:
        hashed_password = pwd_context.hash(user.password)

        create_user_response = await create_new_user(
            data={"name": user.name, "surname": user.surname, "email": user.email,
                  "hashed_password": hashed_password})
        
        if not create_user_response or "id" not in create_user_response:
            raise OrientatiException(details={"message": "User creation failed"},
                                     url="/auth/register")

        user_local = User(
            id=create_user_response["id"],
            email=user.email,
            hashed_password=hashed_password,
            created_at=datetime.fromisoformat(create_user_response["created_at"]),
            updated_at=datetime.fromisoformat(create_user_response["updated_at"]),
            email_verified=False
        )
        db.add(user_local)
        await db.commit()
        await db.refresh(user_local)
        
        return None
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/register", exc=e)


# TODO: Aggiungere job per pulizia sessioni e token scaduti
async def validate_session(access_token: str, db: AsyncSession) -> None:
    try:
        payload = await verify_token(access_token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid access token", InvalidTokenErrorType.INVALID_TOKEN)

        if payload["expired"]:
            stmt = select(Session).where(Session.id == payload["session_id"])
            result = await db.execute(stmt)
            session = result.scalars().first()
            
            if session:
                await db.execute(update(AccessToken).where(AccessToken.session_id == session.id).values(is_expired=True))
                await db.commit()
                raise InvalidTokenException("Access token expired", InvalidTokenErrorType.EXPIRED_SESSION)
            else:
                raise InvalidTokenException("Access token is of an expired session",
                                            InvalidTokenErrorType.EXPIRED_SESSION)
    except (InvalidTokenException, OrientatiException) as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/validate_session", exc=e)


async def get_session_id_from_token(access_token: str) -> str:
    try:
        payload = await verify_token(access_token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid access token", InvalidTokenErrorType.INVALID_TOKEN)
        return payload["session_id"]
    except Exception as e:
        raise e

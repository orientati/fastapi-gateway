from datetime import datetime, timedelta

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
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
        # super().__init__("Unauthorized", message, 401, "/login")

    pass


# Custom exception per invalid session
class InvalidSessionException(OrientatiException):
    def __init__(self, message: str):
        self.message = "Forbidden"
        self.status_code = 403
        self.url = "/logout"
        self.details = {"message": message}
        # super().__init__("Forbidden", message, 403, "/logout")

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
        # super().__init__("Unauthorized", message, 401, "/token/verify")

    pass


async def create_access_token(data: dict, expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES) -> dict:
    """Crea un token di accesso (access token) utilizzando il servizio di autenticazione esterno.

    Args:
        data (dict): Dati da includere nel payload del token.
        expire_minutes (int, optional): Tempo di scadenza in minuti. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Raises:
        OrientatiException: Eccezione sollevata in caso di errore nella richiesta HTTP.

    Returns:
        str: Il token di accesso creato.
    """
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
    """Crea un token di refresh (refresh token) utilizzando il servizio di autenticazione esterno.
    Args:
        data (dict): Dati da includere nel payload del token.
        expire_days (int, optional): Tempo di scadenza in giorni. Defaults to settings.REFRESH_TOKEN_EXPIRE_DAYS.

    Raises:
        OrientatiException: Eccezione sollevata in caso di errore nella richiesta HTTP.

    Returns:
        str: Il token di refresh creato.
    """
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
    """Crea un nuovo utente utilizzando il servizio utenti esterno.

    Args:
        data (dict): Dati dell'utente da creare.

    Raises:
        OrientatiException: Eccezione sollevata in caso di errore nella richiesta HTTP.

    Returns:
        dict: Dati dell'utente creato.
    """
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
            # Se il servizio token risponde con 500, lo trattiamo come token non valido (401)
            # per evitare che il gateway risponda con 500
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
    """
    Crea una sessione per l'utente, genera access e refresh token, li salva nel DB
    e restituisce un TokenResponse.
    """
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
        result = await db.execute(select(User).filter(User.email == user_login.email))
        user = result.scalars().first()

        # Mitigazione attacchi temporali
        password_valid = False
        if user:
            password_valid = verify_password(user_login.password, user.hashed_password)
        else:
            # Simula la verifica per consumare un tempo simile
            verify_password(user_login.password, DUMMY_PWD_HASH)
            password_valid = False

        # Errore generico per tutti i fallimenti di autenticazione (Non trovato, password errata, non verificato)
        if not user or not password_valid:
            raise InvalidCredentialsException()

        if not user.email_verified:
             # Ritorna genericamente 401 anche per email non verificata per prevenire l'enumerazione di utenti "validi ma non verificati"
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

        result_old_token = await db.execute(
            select(RefreshToken).filter(RefreshToken.token == refresh_token.token).join(AccessToken)
        )
        db_old_refresh_token = result_old_token.scalars().first()
        
        if not db_old_refresh_token:
            raise InvalidTokenException("Refresh token not found", InvalidTokenErrorType.TOKEN_NOT_FOUND)

        result_session = await db.execute(select(Session).filter(Session.id == db_old_refresh_token.session_id))
        session = result_session.scalars().first()
        
        if not session or not session.is_active:
            raise InvalidTokenException("Session is inactive or does not exist", InvalidTokenErrorType.INACTIVE_SESSION)
        if session.is_blocked:
            raise InvalidTokenException("Session is blocked", InvalidTokenErrorType.BLOCKED_SESSION)
        if session.expires_at < datetime.now():
            raise InvalidTokenException("Session expired", InvalidTokenErrorType.EXPIRED_SESSION)

        if db_old_refresh_token.is_expired:
            # segno la sessione come non attiva e bloccata, perché è stato riusato un token già usato
            session.is_active = False
            session.is_blocked = True
            await db.commit()
            await db.refresh(session)
            # segno tutti i token associati alla sessione come scaduti
            # await db.execute(update(AccessToken).where(AccessToken.session_id == session.id).values(is_expired=True))
            # await db.execute(update(RefreshToken).where(RefreshToken.session_id == session.id).values(is_expired=True))
            
            # Recupero tutti i token e li aggiorno uno ad uno o uso update massivo se supportato
            # Per semplicità nel refactor usiamo query delete/update
            # In SQLAlchemy async, update requires select or explicit execution.
            # Facciamo fetch and update per ora o raw update
            
            result_access = await db.execute(select(AccessToken).filter(AccessToken.session_id == session.id))
            for at in result_access.scalars().all():
                at.is_expired = True
                
            result_refresh = await db.execute(select(RefreshToken).filter(RefreshToken.session_id == session.id))
            for rt in result_refresh.scalars().all():
                rt.is_expired = True

            await db.commit()

            raise InvalidTokenException("Refresh token expired, Session blocked", InvalidTokenErrorType.EXPIRED_SESSION)

        access_token_response = await create_access_token(
            {"user_id": payload["user_id"], "session_id": session.id})
        refresh_token_response = await create_refresh_token(
            {"user_id": payload["user_id"], "session_id": session.id},
            expire_days=(
                    session.expires_at - datetime.now()).days)
        access_token = access_token_response["token"]
        refresh_token = refresh_token_response["token"]
        # Segno i vecchi token come scaduti
        db_old_refresh_token.is_expired = True
        await db.commit()
        await db.refresh(db_old_refresh_token)
        
        # Access token collegato è in db_old_refresh_token.accessToken (se lazy loaded bisogna fare attenzione)
        # Sarebbe meglio caricare con joinedload se necessario, ma qui proviamo accesso diretto
        # Se fallisce, bisognerà fare una query separata.
        # Proviamo a fare query esplicita per evitare lazy load error in async
        
        if db_old_refresh_token.accessToken:
             # Questo potrebbe fallire se non caricato. 
             # Facciamo query sicura
             pass

        result_at_related = await db.execute(select(AccessToken).filter(AccessToken.id == db_old_refresh_token.accessToken_id))
        at_related = result_at_related.scalars().first()
        if at_related:
             at_related.is_expired = True
             await db.commit() # commit parziale

        # Creo nuovi token
        db_access_token = AccessToken(
            session_id=session.id,
            token=access_token,
        )
        db.add(db_access_token)
        await db.commit()
        await db.refresh(db_access_token)
        db_refresh_token = RefreshToken(
            session_id=session.id,
            token=refresh_token,
            accessToken_id=db_access_token.id
        )
        db.add(db_refresh_token)
        await db.commit()
        await db.refresh(db_refresh_token)

        return TokenResponse(status_code=HttpCodes.CREATED.value, access_token=access_token,
                             refresh_token=refresh_token)
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
            raise InvalidTokenException("Access token expired0", InvalidTokenErrorType.EXPIRED_SESSION)

        result_session = await db.execute(select(Session).filter(Session.id == payload["session_id"]))
        session = result_session.scalars().first()

        if not session:
            raise InvalidSessionException("Session does not exist")

        # Segno la sessione come non attiva
        session.is_active = False
        await db.commit()
        await db.refresh(session)

        # Segno tutti i token associati alla sessione come scaduti
        result_access = await db.execute(select(AccessToken).filter(AccessToken.session_id == session.id))
        for at in result_access.scalars().all():
            at.is_expired = True
            
        result_refresh = await db.execute(select(RefreshToken).filter(RefreshToken.session_id == session.id))
        for rt in result_refresh.scalars().all():
            rt.is_expired = True

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
            # Se 202 Accepted non restituisce contenuto, non possiamo sincronizzare il DB locale. 
            # Assumiamo che il servizio utenti restituisca i dati utente.
            raise OrientatiException(details={"message": "User creation failed"},
                                     url="/auth/register")

        # Salvo l'utente localmente ma NON eseguo il login automatico
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
    """Controlla se il token di accesso è valido e la sessione associata è attiva.

    Args:
        access_token (str): Il token di accesso da convalidare.
        db (AsyncSession): Sessione DB

    Raises:
        InvalidTokenException: Se il token di accesso non è valido.
        InvalidTokenException: Se il token di accesso è scaduto.
        HTTPException: Se si verifica un errore imprevisto durante la convalida.

    Returns:
        bool: True se la sessione è valida, altrimenti False.
    """
    try:
        payload = await verify_token(access_token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid access token", InvalidTokenErrorType.INVALID_TOKEN)

        if payload["expired"]:
            # Segna il token come scaduto
            result_session = await db.execute(select(Session).filter(Session.id == payload["session_id"]))
            session = result_session.scalars().first()
            
            if session:
                # Segna il token access come scaduto
                result_at = await db.execute(select(AccessToken).filter(AccessToken.session_id == session.id))
                for at in result_at.scalars().all():
                     at.is_expired = True

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
    """Estrae l'ID della sessione dal token di accesso.

    Args:
        access_token (str): Il token di accesso.

    Raises:
        InvalidTokenException: Se il token di accesso non è valido.

    Returns:
        str: L'ID della sessione associata al token di accesso.
    """
    try:
        payload = await verify_token(access_token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid access token", InvalidTokenErrorType.INVALID_TOKEN)
        return payload["session_id"]
    except Exception as e:
        raise e

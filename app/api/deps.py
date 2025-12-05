from fastapi.security import OAuth2PasswordBearer

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

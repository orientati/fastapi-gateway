from fastapi.security import OAuth2PasswordBearer
from app.db.session import get_db

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

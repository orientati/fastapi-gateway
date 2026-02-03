

from pydantic import BaseModel


class CittaBase(BaseModel):  # indirizzo di studio
    nome: str
    provincia: str | None = None
    codice_postale: str | None = None


class CittaCreate(CittaBase):
    pass


class CittaUpdate(CittaBase):
    pass


class CittaResponse(CittaBase):
    id: int | None = None


class CittaList(BaseModel):
    citta: list[CittaResponse]
    total: int
    limit: int
    offset: int

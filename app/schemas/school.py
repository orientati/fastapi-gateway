from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr

class SchoolAddress(BaseModel):  # indirizzo di studio
    nome: str
    descrizione: str | None = None
    materie: List[str] = []  # materie insegnate in questo indirizzo


class SchoolBase(BaseModel):
    nome: str
    tipo: str
    indirizzo: str
    città: str
    provincia: str
    codice_postale: str
    email_contatto: EmailStr
    telefono_contatto: str
    indirizzi_scuola: List[SchoolAddress] = []
    sito_web: str | None = None
    descrizione: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(SchoolBase):
    pass


class SchoolsList(BaseModel):
    status_code: int
    scuole: List[SchoolCreate]
    total: int
    limit: int
    offset: int
    filter_search: str | None = None
    filter_tipo: str | None = None
    filter_citta: str | None = None
    filter_provincia: str | None = None
    filter_indirizzo: str | None = None
    sort_by: str | None = None
    order: str | None = None


class SchoolAddress(BaseModel):  # indirizzo di studio
    id: int | None = None
    nome: str
    descrizione: str | None = None
    materie: List[str] = []  # materie insegnate in questo indirizzo


class SchoolBase(BaseModel):
    nome: str
    tipo: str
    indirizzo: str
    email_contatto: EmailStr
    telefono_contatto: str
    sito_web: str | None = None
    descrizione: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SchoolResponse(SchoolBase):
    id: int
    città: str
    provincia: str
    codice_postale: str
    indirizzi_scuola: List[SchoolAddress] = []


class SchoolServiceBase(SchoolBase):
    nome: str
    tipo: str
    indirizzo: str
    email_contatto: EmailStr
    telefono_contatto: str
    sito_web: str | None = None
    descrizione: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    citta_id: int


class SchoolUpdate(SchoolBase):
    id: int
    citta_id: int

class SchoolsList(BaseModel):
    scuole: List[SchoolResponse]
    total: int
    limit: int
    offset: int
    filter_search: str | None = None
    filter_tipo: str | None = None
    filter_citta: str | None = None
    filter_provincia: str | None = None
    filter_indirizzo: str | None = None
    sort_by: str | None = None
    order: str | None = None

class SchoolDeleteResponse(BaseModel):
    message: str = "School deleted successfully"
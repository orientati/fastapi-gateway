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
    email_contatto: EmailStr
    telefono_contatto: str
    sito_web: str | None = None
    descrizione: str | None = None


class SchoolResponse(SchoolBase):
    città: str
    provincia: str
    codice_postale: str
    indirizzi_scuola: List[SchoolAddress] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SchoolCreate(SchoolBase):
    citta_id: int


class SchoolUpdate(SchoolBase):
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
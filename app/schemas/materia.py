

from typing import List

from pydantic import BaseModel


class MateriaBase(BaseModel):
    nome: str
    descrizione: str | None = None


class MateriaResponse(MateriaBase):
    id: int | None = None


class MateriaCreate(MateriaBase):
    pass


class MateriaUpdate(MateriaBase):
    pass


class MateriaList(BaseModel):
    materie: List[MateriaResponse]
    total: int
    offset: int
    limit: int
    filter_search: str | None = None
    sort_by: str | None = None
    order: str | None = None

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import JSONResponse

from app.schemas.citta import CittaList, CittaResponse, CittaUpdate
from app.services import citta as citta_service
from app.services.http_client import OrientatiException

router = APIRouter()


@router.get("/", response_model=CittaList)
async def get_citta(
        limit: int = Query(default=10, ge=1, le=100, description="Numero di città da restituire (1-100)"),
        offset: int = Query(default=0, ge=0, description="Numero di città da saltare per la paginazione"),
        search: Optional[str] = Query(default=None,
                                      description="Termine di ricerca per filtrare le città per nome"),
        sort_by: str = Query(default="name", description="Campo per ordinamento (es. nome)"),
        order: str = Query(default="asc", regex="^(asc|desc)$", description="Ordine: asc o desc")
):
    """
    Recupera la lista delle città, con opzioni di paginazione e filtro.

    Returns:
        CittaList: Lista degli indirizzi con metadati di paginazione
    """
    try:
        return await citta_service.get_citta(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            order=order
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


@router.get("/{citta_id}", response_model=CittaResponse)
async def get_citta(citta_id: int):
    """
    Recupera i dettagli di una città dato il suo ID.

    Args:
        citta_id (int): ID della città da recuperare

    Returns:
        CittaResponse: Dettagli della città
    """
    try:
        return await citta_service.get_citta_by_id(citta_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.get("/zipcode/{zipcode}", response_model=CittaResponse)
async def get_citta_by_zipcode(zipcode: str):
    """
    Recupera i dettagli di una città dato il suo CAP.

    Args:
        zipcode (str): CAP della città da recuperare

    Returns:
        CittaResponse: Dettagli della città
    """
    try:
        return await citta_service.get_citta_by_zipcode(zipcode)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/", response_model=CittaResponse)
async def post_citta(citta: CittaResponse):
    """
    Crea una nuova città.

    Args:
        citta (CittaCreate): Dati della città da creare

    Returns:
        CittaResponse: Dettagli della città creata
    """
    try:
        return await citta_service.post_citta(citta)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.put("/{citta_id}", response_model=CittaResponse)
async def put_citta(citta_id: int, citta: CittaUpdate):
    """
    Aggiorna i dettagli di una città esistente.

    Args:
        citta_id (int): ID della città da aggiornare
        citta (CittaUpdate): Dati aggiornati della città

    Returns:
        CittaResponse: Dettagli della città aggiornata
    """
    try:
        return await citta_service.put_citta(citta_id, citta)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.delete("/{citta_id}")
async def delete_citta(citta_id: int):
    """
    Elimina una città esistente.

    Args:
        citta_id (int): ID della città da eliminare

    Returns:
        MateriaResponse: Dettagli della materia eliminata
    """
    try:
        return await citta_service.delete_citta(citta_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )
   
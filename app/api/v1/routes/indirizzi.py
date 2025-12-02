from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import JSONResponse

from app.schemas.indirizzo import IndirizzoList, IndirizzoResponse, IndirizzoCreate, IndirizzoUpdate
from app.services import indirizzi as indirizzi_service
from app.services.http_client import OrientatiException

router = APIRouter()


@router.get("/", response_model=IndirizzoList)
async def get_indirizzi(
        limit: int = Query(default=10, ge=1, le=100, description="Numero di indirizzi da restituire (1-100)"),
        offset: int = Query(default=0, ge=0, description="Numero di indirizzi da saltare per la paginazione"),
        search: Optional[str] = Query(default=None,
                                      description="Termine di ricerca per filtrare gli indirizzi per nome"),
        sort_by: str = Query(default="name", description="Campo per ordinamento (es. nome)"),
        order: str = Query(default="asc", regex="^(asc|desc)$", description="Ordine: asc o desc")
):
    """
    Recupera la lista delle materie, con opzioni di paginazione e filtro.

    Returns:
        IndirizzoList: Lista degli indirizzi con metadati di paginazione
    """
    try:
        return await indirizzi_service.get_indirizzi(
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


@router.get("/{indirizzo_id}", response_model=IndirizzoResponse)
async def get_indirizzo_by_id(indirizzo_id: int):
    """
    Recupera i dettagli di un indirizzo di studio dato il suo ID.

    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da recuperare

    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio
    """
    try:
        return await indirizzi_service.get_indirizzo_by_id(indirizzo_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/", response_model=IndirizzoResponse)
async def post_indirizzo(indirizzo: IndirizzoCreate):
    """
    Crea un nuovo indirizzo di studio.

    Args:
        indirizzo (IndirizzoCreate): Dati dell'indirizzo di studio da creare

    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio creato
    """
    try:
        return await indirizzi_service.post_indirizzo(indirizzo)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.delete("/{indirizzo_id}")
async def delete_indirizzo(indirizzo_id: int):
    """
    Elimina un indirizzo di studio dato il suo ID.

    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da eliminare

    Returns:
        dict: Messaggio di conferma dell'eliminazione
    """
    try:
        await indirizzi_service.delete_indirizzo(indirizzo_id)
        return {"message": "Indirizzo eliminato con successo"}
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.put("/{indirizzo_id}", response_model=IndirizzoResponse)
async def put_indirizzo(indirizzo_id: int, indirizzo: IndirizzoUpdate):
    """
    Aggiorna i dettagli di un indirizzo di studio esistente.

    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da aggiornare
        indirizzo (IndirizzoUpdate): Dati aggiornati dell'indirizzo di studio

    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio aggiornato
    """
    try:
        return await indirizzi_service.put_indirizzo(indirizzo_id, indirizzo)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )

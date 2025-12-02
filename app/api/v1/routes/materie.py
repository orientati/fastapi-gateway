from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import JSONResponse

from app.schemas.materia import MateriaList, MateriaResponse, MateriaCreate, MateriaUpdate
from app.services import materie as materie_service
from app.services.http_client import OrientatiException

router = APIRouter()


@router.get("/", response_model=MateriaList)
async def get_materie(
        limit: int = Query(default=10, ge=1, le=100, description="Numero di materie da restituire (1-100)"),
        offset: int = Query(default=0, ge=0, description="Numero di materie da saltare per la paginazione"),
        search: Optional[str] = Query(default=None, description="Termine di ricerca per filtrare le materie per nome"),
        sort_by: str = Query(default="name", description="Campo per ordinamento (es. nome)"),
        order: str = Query(default="asc", regex="^(asc|desc)$", description="Ordine: asc o desc")
):
    """
    Recupera la lista delle materie, con opzioni di paginazione e filtro.

    Returns:
        MateriaList: Lista delle materie con metadati di paginazione
    """
    try:
        return await materie_service.get_materie(
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


@router.get("/{materia_id}", response_model=MateriaResponse)
async def get_materia_by_id(materia_id: int):
    """
    Recupera i dettagli di una materia dato il suo ID.

    Args:
        materia_id (int): ID della materia da recuperare

    Returns:
        MateriaResponse: Dettagli della materia
    """
    try:
        return await materie_service.get_materia_by_id(materia_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/", response_model=MateriaResponse)
async def post_materia(materia: MateriaCreate):
    """
    Crea una nuova materia.

    Args:
        materia (MateriaCreate): Dati della materia da creare

    Returns:
        MateriaResponse: Dettagli della materia creata
    """
    try:
        return await materie_service.post_materia(materia)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.put("/{materia_id}", response_model=MateriaResponse)
async def put_materia(materia_id: int, materia: MateriaUpdate):
    """
    Aggiorna i dettagli di una materia esistente.

    Args:
        materia_id (int): ID della materia da aggiornare
        materia (MateriaUpdate): Dati aggiornati della materia

    Returns:
        MateriaResponse: Dettagli della materia aggiornata
    """
    try:
        return await materie_service.put_materia(materia_id, materia)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.delete("/{materia_id}", response_model=dict)
async def delete_materia(materia_id: int):
    """
    Elimina una materia esistente.

    Args:
        materia_id (int): ID della materia da eliminare

    Returns:
        MateriaResponse: Dettagli della materia eliminata
    """
    try:
        return await materie_service.delete_materia(materia_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.post("/link-indirizzo/{materia_id}/{indirizzo_id}")
async def link_materia_to_indirizzo(materia_id: int, indirizzo_id:
int):
    """
    Collega una materia a un indirizzo di studio.

    Args:
        materia_id (int): ID della materia da collegare
        indirizzo_id (int): ID dell'indirizzo di studio a cui collegare la materia
    """
    try:
        return await materie_service.link_materia_to_indirizzo(materia_id, indirizzo_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )


@router.delete("/unlink-indirizzo/{materia_id}/{indirizzo_id}")
async def unlink_materia_from_indirizzo(materia_id: int, indirizzo_id: int):
    """
    Scollega una materia da un indirizzo di studio.

    Args:
        materia_id (int): ID della materia da scollegare
        indirizzo_id (int): ID dell'indirizzo di studio da cui scollegare la materia
    """
    try:
        return await materie_service.unlink_materia_from_indirizzo(materia_id, indirizzo_id)
    except OrientatiException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "message": e.message,
                "details": e.details,
                "url": e.url
            }
        )
   
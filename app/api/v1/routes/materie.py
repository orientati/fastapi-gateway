

from typing import Optional

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import JSONResponse

from app.schemas.materia import MateriaList, MateriaResponse, MateriaCreate, MateriaUpdate
from app.services import materie as materie_service
from app.services.http_client import OrientatiException
from app.core.limiter import limiter
from app.api.deps import validate_token
from fastapi import Request, Depends, Body

router = APIRouter()


@router.get("/", response_model=MateriaList)
@limiter.limit("60/minute")
async def get_materie(
        request: Request,
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
    return await materie_service.get_materie(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        order=order
    )


@router.get("/{materia_id}", response_model=MateriaResponse)
@limiter.limit("60/minute")
async def get_materia_by_id(request: Request, materia_id: int):
    """
    Recupera i dettagli di una materia dato il suo ID.

    Args:
        materia_id (int): ID della materia da recuperare

    Returns:
        MateriaResponse: Dettagli della materia
    """
    return await materie_service.get_materia_by_id(materia_id)


@router.post("/", response_model=MateriaResponse)
@limiter.limit("10/minute")
async def post_materia(request: Request, materia: MateriaCreate = Body(...), payload: dict = Depends(validate_token)):
    """
    Crea una nuova materia.

    Args:
        materia (MateriaCreate): Dati della materia da creare

    Returns:
        MateriaResponse: Dettagli della materia creata
    """
    return await materie_service.post_materia(materia)


@router.put("/{materia_id}", response_model=MateriaResponse)
@limiter.limit("10/minute")
async def put_materia(request: Request, materia_id: int, materia: MateriaUpdate = Body(...), payload: dict = Depends(validate_token)):
    """
    Aggiorna i dettagli di una materia esistente.

    Args:
        materia_id (int): ID della materia da aggiornare
        materia (MateriaUpdate): Dati aggiornati della materia

    Returns:
        MateriaResponse: Dettagli della materia aggiornata
    """
    return await materie_service.put_materia(materia_id, materia)


@router.delete("/{materia_id}", response_model=dict)
@limiter.limit("5/minute")
async def delete_materia(request: Request, materia_id: int, payload: dict = Depends(validate_token)):
    """
    Elimina una materia esistente.

    Args:
        materia_id (int): ID della materia da eliminare

    Returns:
        MateriaResponse: Dettagli della materia eliminata
    """
    return await materie_service.delete_materia(materia_id)


@router.post("/link-indirizzo/{materia_id}/{indirizzo_id}")
@limiter.limit("10/minute")
async def link_materia_to_indirizzo(request: Request, materia_id: int, indirizzo_id:
int, payload: dict = Depends(validate_token)):
    """
    Collega una materia a un indirizzo di studio.

    Args:
        materia_id (int): ID della materia da collegare
        indirizzo_id (int): ID dell'indirizzo di studio a cui collegare la materia
    """
    return await materie_service.link_materia_to_indirizzo(materia_id, indirizzo_id)


@router.delete("/unlink-indirizzo/{materia_id}/{indirizzo_id}")
@limiter.limit("10/minute")
async def unlink_materia_from_indirizzo(request: Request, materia_id: int, indirizzo_id: int, payload: dict = Depends(validate_token)):
    """
    Scollega una materia da un indirizzo di studio.

    Args:
        materia_id (int): ID della materia da scollegare
        indirizzo_id (int): ID dell'indirizzo di studio da cui scollegare la materia
    """
    return await materie_service.unlink_materia_from_indirizzo(materia_id, indirizzo_id)
   
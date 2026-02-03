

from typing import Optional

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import JSONResponse

from app.schemas.indirizzo import IndirizzoList, IndirizzoResponse, IndirizzoCreate, IndirizzoUpdate
from app.services import indirizzi as indirizzi_service
from app.services.http_client import OrientatiException
from app.core.limiter import limiter
from app.api.deps import validate_token
from fastapi import Request, Depends, Body

router = APIRouter()


@router.get("/", response_model=IndirizzoList)
@limiter.limit("60/minute")
async def get_indirizzi(
        request: Request,
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
    return await indirizzi_service.get_indirizzi(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        order=order
    )


@router.get("/{indirizzo_id}", response_model=IndirizzoResponse)
@limiter.limit("60/minute")
async def get_indirizzo_by_id(request: Request, indirizzo_id: int):
    """
    Recupera i dettagli di un indirizzo di studio dato il suo ID.

    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da recuperare

    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio
    """
    return await indirizzi_service.get_indirizzo_by_id(indirizzo_id)


@router.post("/", response_model=IndirizzoResponse)
@limiter.limit("10/minute")
async def post_indirizzo(request: Request, indirizzo: IndirizzoCreate = Body(...), payload: dict = Depends(validate_token)):
    """
    Crea un nuovo indirizzo di studio.

    Args:
        indirizzo (IndirizzoCreate): Dati dell'indirizzo di studio da creare

    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio creato
    """
    return await indirizzi_service.post_indirizzo(indirizzo)


@router.delete("/{indirizzo_id}")
@limiter.limit("5/minute")
async def delete_indirizzo(request: Request, indirizzo_id: int, payload: dict = Depends(validate_token)):
    """
    Elimina un indirizzo di studio dato il suo ID.

    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da eliminare

    Returns:
        dict: Messaggio di conferma dell'eliminazione
    """
    await indirizzi_service.delete_indirizzo(indirizzo_id)
    return {"message": "Indirizzo eliminato con successo"}


@router.put("/{indirizzo_id}", response_model=IndirizzoResponse)
@limiter.limit("10/minute")
async def put_indirizzo(request: Request, indirizzo_id: int, indirizzo: IndirizzoUpdate = Body(...), payload: dict = Depends(validate_token)):
    """
    Aggiorna i dettagli di un indirizzo di studio esistente.

    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da aggiornare
        indirizzo (IndirizzoUpdate): Dati aggiornati dell'indirizzo di studio

    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio aggiornato
    """
    return await indirizzi_service.put_indirizzo(indirizzo_id, indirizzo)

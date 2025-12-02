from app.schemas.citta import CittaList, CittaResponse, CittaCreate, CittaUpdate
from app.services.http_client import HttpMethod, HttpUrl, HttpParams, send_request


async def get_citta(limit, offset, search, sort_by, order) -> CittaList:
    """
    Recupera la lista delle città disponibili.
    Args:
        limit (int): Numero massimo di città da restituire.
        offset (int): Numero di città da saltare per la paginazione.
        search (str | None): Termine di ricerca per filtrare le città per nome.
        sort_by (str | None): Campo per ordinamento (es. nome).
        order (str | None): Ordine: 'asc' o 'desc'.
    Returns:
        CittaList: Lista delle città con metadati di paginazione.
    """
    try:
        params = {
            "limit": limit,
            "offset": offset,
            "search": search,
            "sort_by": sort_by,
            "order": order
        }
        # Rimuovo i parametri None
        params = {k: v for k, v in params.items() if v is not None}

        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint="/citta",
            _params=HttpParams(params)
        )

        return CittaList(**response)
    except Exception as e:
        raise e


async def get_citta_by_id(citta_id: int) -> CittaResponse:
    """
    Recupera i dettagli di una città dato il suo ID.

    Args:
        citta_id (int): ID della città da recuperare

    Returns:
        CittaResponse: Dettagli della città
    """
    try:
        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/citta/{citta_id}"
        )

        return CittaResponse(**response)
    except Exception as e:
        raise e


async def get_citta_by_zipcode(zipcode: str) -> CittaResponse:
    """
    Recupera i dettagli di una città dato il suo CAP.

    Args:
        zipcode (str): CAP della città da recuperare

    Returns:
        CittaResponse: Dettagli della città
    """
    try:
        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/citta/zipcode/{zipcode}"
        )

        return CittaResponse(**response)
    except Exception as e:
        raise e


async def post_citta(citta: CittaCreate) -> CittaResponse:
    """
    Crea una nuova città.

    Args:
        citta (CittaCreate): Dati della città da creare

    Returns:
        CittaResponse: Dettagli della città creata
    """
    try:
        response = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint="/citta",
            _params=HttpParams(citta.model_dump())
        )

        return CittaResponse(**response)
    except Exception as e:
        raise e


async def put_citta(citta_id: int, citta: CittaUpdate) -> CittaResponse:
    """
    Aggiorna i dettagli di una città esistente.

    Args:
        citta_id (int): ID della città da aggiornare
        citta (CittaUpdate): Dati aggiornati della città

    Returns:
        CittaResponse: Dettagli della città aggiornata
    """
    try:
        response = await send_request(
            method=HttpMethod.PUT,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/citta/{citta_id}",
            _params=HttpParams(citta.model_dump())
        )

        return CittaResponse(**response)
    except Exception as e:
        raise e


async def delete_citta(citta_id: int) -> CittaResponse:
    """
    Elimina una città esistente.

    Args:
        citta_id (int): ID della città da eliminare

    Returns:
        CittaResponse: Dettagli della città eliminata
    """
    try:
        response = await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/citta/{citta_id}"
        )

        return CittaResponse(**response)
    except Exception as e:
        raise e

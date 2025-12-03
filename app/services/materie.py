from app.core.logging import get_logger
from app.schemas.materia import MateriaList, MateriaResponse, MateriaCreate, MateriaUpdate
from app.services.http_client import OrientatiException, HttpMethod, HttpUrl, HttpParams, send_request

logger = get_logger(__name__)


async def get_materie(limit, offset, search, sort_by, order) -> MateriaList:
    """
    Recupera la lista delle materie con opzioni di paginazione e filtro.
    Args:
        limit (int): Numero massimo di materie da restituire.
        offset (int): Numero di materie da saltare per la paginazione.
        search (str | None): Termine di ricerca per filtrare le materie per nome.
        sort_by (str | None): Campo per ordinamento (es. nome).
        order (str | None): Ordine: 'asc' o 'desc'.
    Returns:
        MateriaList: Lista delle materie con metadati di paginazione.
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
            endpoint="/materie",
            _params=HttpParams(params)
        )

        return MateriaList(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/materie/get", exc=e)


async def get_materia_by_id(materia_id: int):
    """
    Recupera i dettagli di una materia dato il suo ID.
    Args:
        materia_id (int): ID della materia da recuperare
    Returns:
        MateriaResponse: Dettagli della materia
    """
    try:
        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/materie/{materia_id}"
        )
        return response
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url=f"/materie/{materia_id}", exc=e)


async def post_materia(materia: MateriaCreate) -> MateriaResponse:
    """
    Crea una nuova materia.
    Args:
        materia (MateriaCreate): Dati della materia da creare
    Returns:
        MateriaResponse: Dettagli della materia creata
    """
    try:
        response = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint="/materie",
            _params=HttpParams(materia.model_dump())
        )
        return MateriaResponse(**response)
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/materie/post", exc=e)


async def put_materia(materia_id: int, materia: MateriaUpdate) -> MateriaResponse:
    """
    Aggiorna i dettagli di una materia esistente.
    Args:
        materia_id (int): ID della materia da aggiornare
        materia (MateriaUpdate): Dati aggiornati della materia
    Returns:
        MateriaResponse: Dettagli della materia aggiornata
    """
    try:
        response = await send_request(
            method=HttpMethod.PUT,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/materie/{materia_id}",
            _params=HttpParams(materia.model_dump())
        )
        return MateriaResponse(**response)
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url=f"/materie/put/{materia_id}", exc=e)


async def delete_materia(materia_id: int):
    """
    Elimina una materia esistente.
    Args:
        materia_id (int): ID della materia da eliminare
    """
    try:
        response = await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/materie/{materia_id}"
        )
        return response
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url=f"/materie/delete/{materia_id}", exc=e)


async def link_materia_to_indirizzo(materia_id: int, indirizzo_id: int) -> dict:
    """
    Collega una materia a un indirizzo di studio.
    Args:
        materia_id (int): ID della materia da collegare
        indirizzo_id (int): ID dell'indirizzo di studio a cui collegare la materia
    Returns:
        dict: Dettagli del collegamento creato
    """
    try:

        response = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/materie/link-indirizzo/{materia_id}/{indirizzo_id}"
        )

        return response

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/materie/link_indirizzo", exc=e)


async def unlink_materia_from_indirizzo(materia_id: int, indirizzo_id: int):
    """
    Scollega una materia da un indirizzo di studio.
    Args:
        materia_id (int): ID della materia da scollegare
        indirizzo_id (int): ID dell'indirizzo di studio da cui scollegare la materia
    Returns:
        dict: Dettagli del collegamento rimosso
    """
    try:

        response = await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/materie/unlink-indirizzo/{materia_id}/{indirizzo_id}"
        )

        return response

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/materie/unlink_indirizzo", exc=e)

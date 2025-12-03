from app.schemas.indirizzo import IndirizzoList, IndirizzoResponse, IndirizzoCreate, IndirizzoUpdate
from app.services.http_client import OrientatiException, HttpMethod, HttpUrl, HttpParams, send_request


async def get_indirizzi(limit, offset, search, sort_by, order) -> IndirizzoList:
    """
    Recupera una lista di indirizzi di studio con supporto per paginazione, ricerca e ordinamento.
    Args:
        limit (int): Numero massimo di indirizzi da restituire.
        offset (int): Numero di indirizzi da saltare per la paginazione.
        search (str | None): Termine di ricerca per filtrare gli indirizzi per nome.
        sort_by (str | None): Campo per ordinamento (es. nome).
        order (str | None): Ordine: 'asc' o 'desc'.
    Returns:
        IndirizzoList: Lista degli indirizzi di studio con metadati di paginazione.
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
            endpoint="/indirizzi",
            _params=HttpParams(params)
        )

        return IndirizzoList(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/indirizzi/get", exc=e)


async def get_indirizzo_by_id(indirizzo_id: int) -> IndirizzoResponse:
    """
    Recupera i dettagli di un indirizzo di studio dato il suo ID.
    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da recuperare.
    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio.
    """
    try:
        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/indirizzi/{indirizzo_id}"
        )

        return IndirizzoResponse(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url=f"/indirizzi/{indirizzo_id}", exc=e)


async def post_indirizzo(indirizzo_data: IndirizzoCreate) -> IndirizzoResponse:
    """
    Crea un nuovo indirizzo di studio.
    Args:
        indirizzo_data (IndirizzoCreate): Dati dell'indirizzo di studio da creare.
    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio creato.
    """
    try:
        response = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint="/indirizzi",
            _params=HttpParams(indirizzo_data.model_dump())
        )

        return IndirizzoResponse(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/indirizzi/post", exc=e)


async def put_indirizzo(indirizzo_id: int, indirizzo_data: IndirizzoUpdate) -> IndirizzoResponse:
    """
    Aggiorna i dettagli di un indirizzo di studio esistente.
    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da aggiornare.
        indirizzo_data (IndirizzoUpdate): Dati aggiornati dell'indirizzo di studio.
    Returns:
        IndirizzoResponse: Dettagli dell'indirizzo di studio aggiornato.
    """
    try:
        response = await send_request(
            method=HttpMethod.PUT,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/indirizzi/{indirizzo_id}",
            _params=HttpParams(indirizzo_data.model_dump())
        )

        return IndirizzoResponse(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url=f"/indirizzi/put/{indirizzo_id}", exc=e)


async def delete_indirizzo(indirizzo_id: int) -> None:
    """
    Elimina un indirizzo di studio esistente.
    Args:
        indirizzo_id (int): ID dell'indirizzo di studio da eliminare.
    Returns:
        None
    """
    try:
        await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/indirizzi/{indirizzo_id}"
        )

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url=f"/indirizzi/delete/{indirizzo_id}", exc=e)

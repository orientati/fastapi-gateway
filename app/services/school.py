from typing import Optional

from app.core.logging import get_logger
from app.schemas.school import SchoolsList, SchoolCreate, SchoolResponse
from app.services.http_client import OrientatiException, HttpMethod, HttpUrl, HttpParams, send_request

logger = get_logger(__name__)


async def get_schools(
        limit: int = 10,
        offset: int = 0,
        search: Optional[str] = None,
        tipo: Optional[str] = None,
        citta: Optional[str] = None,
        provincia: Optional[str] = None,
        indirizzo: Optional[str] = None,
        sort_by: str = "name",
        order: str = "asc"
) -> SchoolsList:
    """
    Recupera la lista delle scuole con opzioni di paginazione e filtro.

    Args:
        limit (int): Numero massimo di scuole da restituire.
        offset (int): Numero di scuole da saltare per la paginazione.
        search (Optional[str]): Termine di ricerca per filtrare le scuole per nome.
        tipo (Optional[str]): Filtra per tipo di scuola (es. Liceo, ITIS, ecc.).
        citta (Optional[str]): Filtra per città.
        provincia (Optional[str]): Filtra per provincia.
        indirizzo (Optional[str]): Filtra per tipo di studi (es. liceo classico, informatico, ecc.).
        sort_by (str): Campo per ordinamento (es. nome, città, provincia).
        order (str): Ordine: 'asc' o 'desc'.

    Returns:
        SchoolsList: Lista delle scuole con metadati di paginazione.
    """
    try:
        params = {
            "limit": limit,
            "offset": offset,
            "search": search,
            "tipo": tipo,
            "citta": citta,
            "provincia": provincia,
            "indirizzo": indirizzo,
            "sort_by": sort_by,
            "order": order
        }
        # Rimuovo i parametri None
        params = {k: v for k, v in params.items() if v is not None}

        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint="/schools",
            _params=HttpParams(params)
        )

        return SchoolsList(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/register", exc=e)


async def get_school_by_id(school_id: int):
    """
    Recupera i dettagli di una scuola specifica tramite il suo ID.

    Args:
        school_id (int): ID della scuola da recuperare.

    Returns:
        dict: Dettagli della scuola.
    """
    try:
        response = await send_request(
            method=HttpMethod.GET,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/schools/{school_id}"
        )

        return response

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/register", exc=e)


async def create_school(school: SchoolCreate) -> SchoolResponse:
    """
    Crea una nuova scuola.

    Args:
        school (SchoolCreate): Dati della scuola da creare.

    Returns:
        dict: Dettagli della scuola creata.
    """
    try:
        params = school.model_dump()

        response = await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint="/schools",
            _params=HttpParams(params)
        )

        return SchoolResponse(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/register", exc=e)


async def update_school(school_id, school) -> SchoolResponse:
    """
    Aggiorna i dettagli di una scuola esistente.

    Args:
        school_id (int): ID della scuola da aggiornare.
        school (SchoolCreate): Dati aggiornati della scuola.

    Returns:
        dict: Dettagli della scuola aggiornata.
    """
    try:
        params = school.model_dump()

        response = await send_request(
            method=HttpMethod.PUT,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/schools/{school_id}",
            _params=HttpParams(params)
        )

        return SchoolResponse(**response)

    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/register", exc=e)


async def delete_school(school_id):
    """
    Elimina una scuola esistente.

    Args:
        school_id (int): ID della scuola da eliminare.

    Returns:
        None
    """
    try:
        return await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.SCHOOLS_SERVICE,
            endpoint=f"/schools/{school_id}"
        )
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(url="/auth/register", exc=e)

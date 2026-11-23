import logging
import os
import uuid
from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select, text
from supabase import Client, create_client

from schemas.schemas_cat import CatPhotos, Cats
from services.connection import engine, get_connection
from services.save_embedding import save_cat_embedding
from services.yolo_service import crop_img

load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cats")

#----------------------------------------- G E T -----------------------------------------

@router.get("/", status_code=status.HTTP_200_OK)
async def get_cats(session: Session = Depends(get_connection)):
    try:
        results = session.exec(select(Cats)).all()
        return {
            "msg": "Información de gatos obtenida con éxito.",
            "info": results,
        }
    except Exception as e:
        logger.error(f"Error al consultar gatos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos obtener la lista de gatos en este momento.",
        )

@router.get("/photos/", status_code=status.HTTP_200_OK)
async def get_cat_photos(session: Session = Depends(get_connection)):
    try:
        results = session.exec(select(CatPhotos)).all()
        return {
            "msg": "Fotos obtenidas con éxito.",
            "info": results,
        }
    except Exception as e:
        logger.error(f"Error al consultar fotos de gatos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos obtener las fotos en este momento.",
        )

@router.get("/{cat_id}", status_code=status.HTTP_200_OK)
async def get_cat_by_id(cat_id: uuid.UUID, session: Session = Depends(get_connection)):
    try:
        cat = session.get(Cats, cat_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No encontramos un gato con ese identificador.",
            )

        return {
            "msg": "Información del gato obtenida con éxito.",
            "info": cat,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al consultar gato {cat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos consultar la información de este gato.",
        )

@router.get("/{actor_id}/cat_photos", status_code=status.HTTP_200_OK)
def get_cat_by_actor_id(actor_id: uuid.UUID, session: Session = Depends(get_connection)):
    try:
        statement = (
            select(Cats, CatPhotos)
            .outerjoin(CatPhotos, Cats.id == CatPhotos.cat_id)
            .where(Cats.actor_id == actor_id)
        )
        rows = session.exec(statement).all()

        cats_map = {}
        for cat, photo in rows:
            if cat.id not in cats_map:
                cat_data = cat.model_dump()
                cat_data["photos"] = []
                cats_map[cat.id] = cat_data

            if photo is not None:
                cats_map[cat.id]["photos"].append(photo.image_url)

        cats_list = []
        for cat_data in cats_map.values():
            cat_data["photos_count"] = len(cat_data["photos"])
            cats_list.append(cat_data)

        return {
            "msg": "Información de gatos y fotos obtenida con éxito.",
            "info": {"cats": cats_list},
        }
    except Exception as e:
        logger.error(f"Error al consultar gatos del actor {actor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos cargar los gatos y sus fotos.",
        )
    
#----------------------------------------- P O S T -----------------------------------------

@router.post("/register/cat/", status_code=status.HTTP_201_CREATED)
async def register(cats_data: Cats, session: Session = Depends(get_connection)):
    try:
        session.add(cats_data)
        session.commit()
        session.refresh(cats_data)

        return {
            "msg": "Gato registrado con éxito.",
            "info": cats_data.model_dump(),
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error al registrar gato: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo registrar el gato. Revisa los datos enviados o si ya registraste un gato con ese mismo nombre.",
        )

@router.post("/register/photo/", status_code=status.HTTP_201_CREATED)
async def upload_cat_photo(
    background_tasks: BackgroundTasks,
    cat_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_connection),
):
    allowed_content_types = ["image/jpeg", "image/jpg"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no permitido. Solo aceptamos imágenes JPG o JPEG.",
        )

    file_extension = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else ""
    if file_extension not in ["jpg", "jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La extensión del archivo debe ser .jpg o .jpeg.",
        )

    cat = session.get(Cats, cat_id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El gato indicado no existe.",
        )

    existing_photos = session.exec(
        select(CatPhotos).where(CatPhotos.cat_id == cat_id)
    ).all()
    MAX_PHOTOS = 5
    if len(existing_photos) >= MAX_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Llegaste al límite de {MAX_PHOTOS} fotos para este michi. Borra alguna si quieres subir otra.",
        )

    file_uploaded = False
    file_path = None
    bucket_name = "cat-photos"

    try:
        file_bytes = await file.read()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"cats/{unique_filename}"

        cat_detection = crop_img(file_bytes=file_bytes)
        if not cat_detection["True"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=cat_detection.get("msg") or "No pudimos detectar un gato válido en la imagen.",
            )

        cropped_bytes = cat_detection["cropped_image"]
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=cropped_bytes,
            file_options={"content-type": file.content_type},
        )
        file_uploaded = True

        image_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

        new_photo = CatPhotos(
            cat_id=cat_id,
            image_url=image_url,
        )
        session.add(new_photo)
        session.commit()
        session.refresh(new_photo)

        background_tasks.add_task(
            save_cat_embedding,
            cat_id=cat_id,
            photo_id=new_photo.id,
            image_bytes=cropped_bytes,
            db_engine=engine,
        )

        return {
            "message": "Foto registrada con éxito.",
            "info": "¡Anotada! Si le tomas fotos siempre desde el mismo lado, el sistema no va a poder reconocer sus marcas únicas.",
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error al subir/procesar foto del gato {cat_id}: {e}")
        if file_uploaded and file_path:
            try:
                supabase.storage.from_(bucket_name).remove([file_path])
            except Exception as cleanup_error:
                logger.warning(f"No se pudo limpiar imagen huérfana {file_path}: {cleanup_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un problema al procesar y guardar la imagen. Intenta de nuevo.",
        )

def get_cat_embedding_ids(session: Session, cat_id: uuid.UUID) -> list[uuid.UUID]:
    rows = session.exec(
        text("SELECT id FROM embeddings_cats WHERE cat_id = :cat_id"),
        params={"cat_id": str(cat_id)},
    ).all()
    return [row[0] for row in rows]


@router.get("/matches/cat/{cat_id}", status_code=status.HTTP_200_OK)
def get_cat_matches_by_cat(
    cat_id: uuid.UUID,
    session: Session = Depends(get_connection),
):
    embedding_ids = get_cat_embedding_ids(session, cat_id)[:5]

    if not embedding_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este gato aún no tiene embeddings listos para buscar coincidencias.",
        )

    query = text("""
    WITH target AS (
        SELECT embedding AS vec
        FROM embeddings_cats
        WHERE id = :target_embedding_id
    ),
    ranked_by_cat AS (
        SELECT DISTINCT ON (c.id)
            c.id AS cat_id,
            c.name AS name,
            c.actor_type AS actor_type,
            pc.image_url AS image_url,
            COALESCE(f.email, col.email) AS contact_email,
            COALESCE(f.created_at, col.created_at) AS actor_created_at,
            (ec.embedding <=> t.vec) AS distancia_coseno,
            ROUND(((1 - (ec.embedding <=> t.vec)) * 100)::numeric, 2) AS similitud
        FROM cats AS c
        INNER JOIN embeddings_cats AS ec
            ON c.id = ec.cat_id
        LEFT JOIN photos_cats AS pc
            ON ec.photo_id = pc.id
        LEFT JOIN foundations AS f
            ON c.actor_type = 'foundation' AND c.actor_id = f.id
        LEFT JOIN collaborators AS col
            ON c.actor_type = 'collaborator' AND c.actor_id = col.id
        CROSS JOIN target AS t
        WHERE c.actor_type IN ('foundation', 'collaborator')
            AND c.id <> :query_cat_id
        ORDER BY c.id, distancia_coseno ASC
    )
    SELECT
        cat_id,
        name,
        actor_type,
        image_url,
        contact_email,
        actor_created_at,
        similitud
    FROM ranked_by_cat
    ORDER BY distancia_coseno ASC
    LIMIT 5;
    """)

    best_by_candidate: dict[str, dict] = {}

    try:
        for emb_id in embedding_ids:
            rows = session.exec(
                query,
                params={
                    "target_embedding_id": str(emb_id),
                    "query_cat_id": str(cat_id),
                },
            ).mappings().all()

            for r in rows:
                cand_id = str(r["cat_id"])
                sim = float(r["similitud"])
                if cand_id not in best_by_candidate or sim > best_by_candidate[cand_id]["similitud"]:
                    created_at = r["actor_created_at"]
                    best_by_candidate[cand_id] = {
                        "cat_id": cand_id,
                        "name": r["name"],
                        "actor_type": r["actor_type"],
                        "image_url": r["image_url"],
                        "email": r["contact_email"],
                        "created_at": created_at.isoformat() if created_at else None,
                        "similitud": sim,
                    }

        matches = sorted(
            best_by_candidate.values(),
            key=lambda x: x["similitud"],
            reverse=True,
        )[:25]

        return {"matches": matches}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al buscar coincidencias para el gato {cat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos calcular las coincidencias en este momento. Intenta de nuevo.",
        )

#----------------------------------------- D E L E T E -----------------------------------------

def _extract_storage_path(image_url: str, bucket_name: str = "cat-photos") -> str | None:
    if not image_url:
        return None
    marker = f"/{bucket_name}/"
    if marker in image_url:
        return image_url.split(marker, 1)[1].split("?", 1)[0]
    return None


@router.delete("/delete_photo/{photo_id}", status_code=status.HTTP_200_OK)
def delete_cat_photo(
    photo_id: uuid.UUID,
    session: Session = Depends(get_connection),
):
    photo = session.get(CatPhotos, photo_id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos esa foto.",
        )

    bucket_name = "cat-photos"
    file_path = _extract_storage_path(photo.image_url, bucket_name=bucket_name)

    try:

        session.exec(
            text("DELETE FROM embeddings_cats WHERE photo_id = :photo_id"),
            params={"photo_id": str(photo_id)},
        )

        session.delete(photo)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error al eliminar registro/embeddings de la foto {photo_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos eliminar la foto en este momento. Intenta de nuevo.",
        )

    if file_path:
        try:
            supabase.storage.from_(bucket_name).remove([file_path])
        except Exception as storage_err:
            logger.warning(f"Se borró de BD pero falló borrar en Storage ({file_path}): {storage_err}")

    return {
        "msg": "Foto eliminada con éxito.",
        "data": {"photo_id": str(photo_id)},
    }

@router.delete("/delete_cat/{cat_id}", status_code=status.HTTP_200_OK)
async def delete_cat(
    cat_id: uuid.UUID,
    session: Session = Depends(get_connection),
):
    cat = session.get(Cats, cat_id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos este gato.",
        )

    bucket_name = "cat-photos"
    photos = session.exec(
        select(CatPhotos).where(CatPhotos.cat_id == cat_id)
    ).all()

    file_paths = [
        path
        for photo in photos
        if (path := _extract_storage_path(photo.image_url, bucket_name=bucket_name))
    ]

    try:
        session.delete(cat)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error al eliminar el gato {cat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos eliminar este gato en este momento. Intenta de nuevo.",
        )

    if file_paths:
        try:
            supabase.storage.from_(bucket_name).remove(file_paths)
        except Exception as storage_err:
            logger.warning(
                f"Gato {cat_id} eliminado de BD, pero falló borrar archivos en Storage ({file_paths}): {storage_err}"
            )

    return {
        "msg": "Gato y sus registros asociados eliminados con éxito.",
        "data": {
            "cat_id": str(cat_id),
            "deleted_photos_count": len(photos),
        },
    }
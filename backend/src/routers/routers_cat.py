from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import bindparam, text
from sqlmodel import text, Session, select
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

import uuid
import os

from services.connection import get_connection, engine
from services.yolo_service import crop_img
from services.save_embedding import save_cat_embedding
from schemas.schemas_cat import Cats, CatPhotos, CatEmbeddings
from services.embedding_service import embedding_service

load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
router = APIRouter(prefix="/cats")


#----------------------------------------- G E T -----------------------------------------

@router.get("/", status_code=status.HTTP_200_OK)
async def get_cats(session: Session = Depends(get_connection)):
    try: 
        statement = select(Cats)
        results = session.exec(statement).all()

        return {
            'msg': 'The cats information was resolver succesfully',
            'info': results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The cats information could not be resolved: {str(e)}"
        )

@router.get("/photos/", status_code=status.HTTP_200_OK)
async def get_cats(session: Session = Depends(get_connection)):
    try: 
        statement = select(CatPhotos)
        results = session.exec(statement).all()

        return {
            'msg': 'The cats information was resolver succesfully',
            'info': results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The cats information could not be resolved: {str(e)}"
        )

@router.get("/{cat_id}", status_code=status.HTTP_200_OK)
async def get_cat_by_id(cat_id: uuid.UUID, session: Session = Depends(get_connection)):
    try:
        cat = session.get(Cats, cat_id)
        
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cat with id {cat_id} not found"
            )
            
        return {
            'msg': 'The cat information was resolved successfully',
            'info': cat
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The cat information could not be resolved: {str(e)}"
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
            count = len(cat_data["photos"])
            cat_data["photos_count"] = count
            cats_list.append(cat_data)

        return {
            "msg": 'The cat information was resolved successfully',
            "info": {
                "cats": cats_list
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The cat information could not be resolved: {str(e)}"
        )

#----------------------------------------- P O S T -----------------------------------------

@router.post('/register/cat/', status_code=status.HTTP_201_CREATED)
async def register(cats_data: Cats, session: Session = Depends(get_connection)):
    try: 
        session.add(cats_data)
        session.commit()
        session.refresh(cats_data)

        new_cat_record = dict(cats_data)

        return {
            'msg': 'Cat created succesfully.',
            'info': new_cat_record
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register Cat: {str(e)}"
        )

@router.post('/register/photo/', status_code=status.HTTP_201_CREATED)
async def upload_cat_photo(
        background_tasks: BackgroundTasks,
        cat_id: uuid.UUID = Form(...),
        file: UploadFile = File(...),
        session: Session = Depends(get_connection)
    ):
    allowed_content_types = ["image/jpeg", "image/jpg"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no permitido. Solo se aceptan imágenes en formato JPG o JPEG."
        )

    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_extension not in ["jpg", "jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La extensión del archivo debe ser .jpg o .jpeg."
        )

    file_uploaded = False    
    file_path = None
    bucket_name = "cat-photos"

    try:
        existing_photos = session.exec(
            select(CatPhotos).where(CatPhotos.cat_id == cat_id)
        ).all()
        
        current_count = len(existing_photos)
        MAX_PHOTOS = 5

        if current_count >= MAX_PHOTOS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"llegaste al límite de {MAX_PHOTOS} fotos para este michi. ¡Borrame alguna si quieres subir otra nueva!"
            )
        
        file_bytes = await file.read()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"cats/{unique_filename}"

        cat_detecction_bytes = crop_img(file_bytes=file_bytes)
        if not cat_detecction_bytes["True"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=cat_detecction_bytes["msg"]
            )

        file_bytes = cat_detecction_bytes["cropped_image"]
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        file_uploaded = True

        image_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

        new_photo = CatPhotos(
            cat_id=cat_id,
            image_url=image_url
        )
        
        session.add(new_photo)
        session.commit()
        session.refresh(new_photo)

        background_tasks.add_task(
            save_cat_embedding,
            cat_id=cat_id,
            photo_id=new_photo.id, 
            image_bytes=file_bytes,
            db_engine=engine,
        )

        return {
            "message": "Foto registrada con éxito.",
            "info": f"¡Anotada!\
                Si le tomas fotos siempre desde el mismo lado,\
                el sistema no va a poder reconocer sus marcas únicas.",
        }
    except HTTPException:     
        raise
    except Exception as e:
        session.rollback()
        if file_uploaded:
            try:
                supabase.storage.from_(bucket_name).remove([file_path])
            except Exception as cleanup_error:
                print(f"Error al limpiar la imagen huérfana: {cleanup_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la imagen: {str(e)}"
        )

@router.get("/matches/{embedding_id}", status_code=status.HTTP_200_OK)
def get_cat_matches_by_embedding(
    embedding_id: uuid.UUID,
    session: Session = Depends(get_connection),
):
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
                (ec.embedding <=> t.vec) AS distancia_coseno,
                ROUND(((1 - (ec.embedding <=> t.vec)) * 100)::numeric, 2) AS similitud
            FROM cats AS c
            INNER JOIN embeddings_cats AS ec
                ON c.id = ec.cat_id
            LEFT JOIN photos_cats AS pc
                ON ec.photo_id = pc.id
            CROSS JOIN target AS t
            WHERE c.actor_type IN ("foundation", "colaborator")
              AND ec.id <> :target_embedding_id
            ORDER BY c.id, distancia_coseno ASC
        )
        SELECT
            cat_id,
            name,
            actor_type,
            image_url,
            similitud
        FROM ranked_by_cat
        ORDER BY distancia_coseno ASC
        LIMIT 5;
    """).bindparams(bindparam("actor_types", expanding=True))

    try:
        rows = session.exec(
            query,
            params={
                "target_embedding_id": str(embedding_id)
            },
        ).mappings().all()

        return {
            "matches": [
                {
                    "cat_id": str(r["cat_id"]),
                    "name": r["name"],
                    "actor_type": r["actor_type"],
                    "image_url": r["image_url"],
                    "similitud": float(r["similitud"]),
                }
                for r in rows
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al consultar coincidencias: {str(e)}",
        )
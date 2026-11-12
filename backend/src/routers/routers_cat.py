from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from sqlmodel import text, Session, select
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

import uuid
import os

from services.connection import get_connection
from schemas.schemas_cat import Cats, CatPhotos

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
            'data': new_cat_record
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register Cat: {str(e)}"
        )

@router.post('/register/photos/', status_code=status.HTTP_201_CREATED)
async def upload_cat_photo(
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

    try:
        file_bytes = await file.read()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"cats/{unique_filename}"
        bucket_name = "cat-photos"

        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )

        image_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

        new_photo = CatPhotos(
            cat_id=cat_id,
            image_url=image_url
        )
        
        session.add(new_photo)
        session.commit()
        session.refresh(new_photo)

        return {
            "message": "Foto registrada con éxito.",
            "data": new_photo.model_dump()
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la imagen: {str(e)}"
        )
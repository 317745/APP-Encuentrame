from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import text, Session, select

import uuid

from services.connection import get_connection
from schemas.schemas_cat import Cats, CatPhotos

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

@router.post('/register/photo/', status_code=status.HTTP_201_CREATED)
async def upload_cat_photo(photo_data: CatPhotos, session: Session = Depends(get_connection)):
    try:
        session.add(photo_data)
        session.commit()
        session.refresh(photo_data)

        return {
            'msg': 'Cat photo uploaded successfully.',
            'data': photo_data.model_dump()
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not upload cat photo: {str(e)}"
        )

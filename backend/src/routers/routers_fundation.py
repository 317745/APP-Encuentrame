from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import text, Session, select

from services.connection import get_connection
from schemas.schemas_fundaction import AuthFoundation, Foundation

router = APIRouter(prefix='/fundations')

#----------------------------------------- G E T -----------------------------------------

@router.get("/", status_code=status.HTTP_200_OK)
async def get_fundations(session: Session = Depends(get_connection)):
    try:
        statement = select(Foundation)
        results = session.exec(statement).all()

        return {
            'msg': 'The foundation information was resolved successfully',
            'info': results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The foundation information could not be resolved: {str(e)}"
        )
          
#----------------------------------------- P O S T -----------------------------------------

@router.post("/register/auth/", status_code=status.HTTP_201_CREATED)
def register_auth(auth_data: AuthFoundation, session: Session = Depends(get_connection)):
    try:
        session.add(auth_data)
        session.commit()
        session.refresh(auth_data)
        
        new_auth_record = dict(auth_data)

        return {
            'msg': 'Auth credential created successfully. Use this ID to create your foundation profile.',
            'data': new_auth_record
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register auth credential (email might already exist): {str(e)}"
        )

@router.post("/register/profile/", status_code=status.HTTP_201_CREATED)
def register_foundation(foundation_data: Foundation, session: Session = Depends(get_connection)):
    try:
        session.add(foundation_data)
        session.commit()
        session.refresh(foundation_data)
        
        new_foundation_record = dict(foundation_data)

        return {
            'msg': 'Foundation profile created successfully.',
            'data': new_foundation_record
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register foundation profile: {str(e)}"
        )
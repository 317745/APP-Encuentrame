from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import text, Session, select

from services.connection import get_connection
from schemas.schemas_user import User, AuthUser

router = APIRouter(prefix='/users')

#----------------------------------------- G E T -----------------------------------------

@router.get("/", status_code=status.HTTP_200_OK)
async def get_users(session: Session = Depends(get_connection)):
    try:
        statement = select(User)
        results = session.exec(statement)

        return {
            'msg': 'The users information was resolved successfully',
            'info': results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The users information could not be resolved: {str(e)}"
        )

#----------------------------------------- P O S T -----------------------------------------

@router.post("/register/auth/", status_code=status.HTTP_201_CREATED)
async def register_auth(auth_data: AuthUser, session: Session = Depends(get_connection)):
    try:
        session.add(auth_data)
        session.commit()
        session.refresh(auth_data)

        new_auth_record = dict(auth_data)

        return {
            'msg': 'Auth credential created successfully. Use this ID to create your user profile.',
            'data': new_auth_record
        }
    
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register auth credential (email might already exist): {str(e)}"
        )

@router.post("/register/profile/", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: User, session: Session = Depends(get_connection)):
    try:
        session.add(user_data)
        session.commit()
        session.refresh(user_data)

        new_user_record = dict(user_data)

        return {
            'msg': 'User profile created successfully.',
            'data': new_user_record
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register user profile: {str(e)}"
        )
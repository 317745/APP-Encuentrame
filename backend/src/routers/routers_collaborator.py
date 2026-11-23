import logging
from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select

from services.connection import get_connection
from schemas.schemas_collaborator import AuthCollaborator, Collaborator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collaborator")


# ----------------------------------------- P O S T -----------------------------------------

@router.post("/register/auth/", status_code=status.HTTP_201_CREATED)
def register_auth(auth_data: AuthCollaborator, session: Session = Depends(get_connection)):
    existing = session.exec(
        select(AuthCollaborator).where(AuthCollaborator.email == auth_data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese correo ya está registrado. Intenta iniciar sesión o usa otro correo."
        )

    try:
        session.add(auth_data)
        session.commit()
        session.refresh(auth_data)

        return {
            "msg": "Credenciales creadas con éxito. Usa este ID para completar tu perfil de colaborador.",
            "data": {
                "id": str(auth_data.id),
                "email": auth_data.email,
            }
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error al registrar auth de colaborador: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos crear tus credenciales en este momento. Intenta de nuevo más tarde."
        )


@router.post("/register/profile/", status_code=status.HTTP_201_CREATED)
def register_collaborator(collaborator_data: Collaborator, session: Session = Depends(get_connection)):
    try:
        session.add(collaborator_data)
        session.commit()
        session.refresh(collaborator_data)

        return {
            "msg": "Perfil de colaborador creado con éxito.",
            "data": collaborator_data.model_dump()
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error al registrar perfil de colaborador: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo guardar tu perfil. Revisa que los datos estén completos y que este ID no tenga ya un perfil."
        )


@router.post("/login/", status_code=status.HTTP_200_OK)
async def login(credentials: AuthCollaborator, session: Session = Depends(get_connection)):
    auth = session.exec(
        select(AuthCollaborator).where(AuthCollaborator.email == credentials.email)
    ).first()

    if not auth or auth.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos."
        )

    collaborator = session.get(Collaborator, auth.id)

    return {
        "msg": "Inicio de sesión exitoso.",
        "data": {
            "id": str(auth.id),
            "email": auth.email,
            "name": collaborator.name if collaborator else None,
            "created_at": collaborator.created_at if collaborator else None,
            "actor_type": "collaborator"
        }
    }
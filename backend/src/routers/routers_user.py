import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from schemas.schemas_user import AuthUser, User
from services.connection import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users")


# ----------------------------------------- G E T -----------------------------------------

@router.get("/", status_code=status.HTTP_200_OK)
async def get_users(session: Session = Depends(get_connection)):
    try:
        results = session.exec(select(User)).all()
        return {
            "msg": "Información de usuarios obtenida con éxito.",
            "info": results,
        }
    except Exception as e:
        logger.error(f"Error al consultar usuarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos obtener la lista de usuarios en este momento.",
        )


# ----------------------------------------- P O S T -----------------------------------------

@router.post("/register/auth/", status_code=status.HTTP_201_CREATED)
async def register_auth(auth_data: AuthUser, session: Session = Depends(get_connection)):
    existing = session.exec(
        select(AuthUser).where(AuthUser.email == auth_data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese correo ya está registrado. Intenta iniciar sesión o usa otro correo.",
        )

    try:
        session.add(auth_data)
        session.commit()
        session.refresh(auth_data)

        return {
            "msg": "Credenciales creadas con éxito. Usa este ID para completar tu perfil de usuario.",
            "data": {
                "id": str(auth_data.id),
                "email": auth_data.email,
            },
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error al registrar auth de usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos crear tus credenciales en este momento. Intenta de nuevo más tarde.",
        )


@router.post("/register/profile/", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: User, session: Session = Depends(get_connection)):
    try:
        session.add(user_data)
        session.commit()
        session.refresh(user_data)

        return {
            "msg": "Perfil de usuario creado con éxito.",
            "data": user_data.model_dump(),
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error al registrar perfil de usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo guardar tu perfil. Revisa los datos enviados o si este ID ya tiene un perfil.",
        )


@router.post("/login/", status_code=status.HTTP_200_OK)
async def login(credentials: AuthUser, session: Session = Depends(get_connection)):
    auth = session.exec(
        select(AuthUser).where(AuthUser.email == credentials.email)
    ).first()

    if not auth or auth.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    user = session.get(User, auth.id)

    return {
        "msg": "Inicio de sesión exitoso.",
        "data": {
            "id": str(auth.id),
            "email": auth.email,
            "name": user.name if user else None,
            "created_at": user.created_at if user else None,
            "actor_type": "user",
        },
    }
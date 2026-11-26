# Reemplaza tu endpoint /{cat_id}/photos/ en routers_cat.py por este.

@router.get("/{cat_id}/photos/", status_code=status.HTTP_200_OK)
async def get_photos_by_cat_id(cat_id: uuid.UUID, session: Session = Depends(get_connection)):
    try:
        # session.get() busca UNA fila por su llave primaria (el id de la foto) y no tiene .all().
        # Para "todas las fotos de este gato" se filtra por cat_id con select().
        photos = session.exec(
            select(CatPhotos).where(CatPhotos.cat_id == cat_id)
        ).all()

        if not photos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay fotos del gatito registradas.",
            )

        return {
            "msg": "Fotos obtenidas con éxito.",
            "info": photos,
        }
    except HTTPException:      # sin esto, el 404 de arriba se convierte en 500
        raise
    except Exception as e:
        logger.error(f"Error al consultar fotos del gato {cat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No pudimos obtener las fotos en este momento.",
        )

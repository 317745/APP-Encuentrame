from sqlmodel import Session
from services.embedding_service import embedding_service
from schemas.schemas_cat import CatEmbeddings

def save_cat_embedding(cat_id,  photo_id, image_bytes: bytes, db_engine) -> None:
    vector_512 = embedding_service.get_embedding(image_bytes)

    with Session(db_engine) as session:
        record = CatEmbeddings(
            cat_id=cat_id,
            photo_id=photo_id,
            embedding=vector_512,
        )
        session.add(record)
        session.commit()
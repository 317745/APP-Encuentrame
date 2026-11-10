from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, text

from services.connection import verify_connection, engine

from schemas.schemas_cat import Cats, CatPhotos
from schemas.schemas_fundaction import Foundation, AuthFoundation

from routers import routers_fundation, routers_cat

@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_connection()
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
     
app.include_router(routers_fundation.router)
app.include_router(routers_cat.router)

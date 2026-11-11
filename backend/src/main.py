from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, text

from services.connection import verify_connection, engine

from schemas.schemas_cat import Cats, CatPhotos
from schemas.schemas_fundation import Foundation, AuthFoundation
from schemas.schemas_user import User, AuthUser

from routers import routers_fundation, routers_cat, routers_user

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
app.include_router(routers_user.router)
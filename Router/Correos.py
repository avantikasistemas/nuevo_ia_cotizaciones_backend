from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Correos import Correos
from Utils.decorator import http_decorator
from Config.db import get_db

correos_router = APIRouter()


@correos_router.post('/listar', tags=["Correos"])
@http_decorator
def listar(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return Correos(db).listar(data)


@correos_router.post('/detalle', tags=["Correos"])
@http_decorator
def detalle(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return Correos(db).detalle(data)

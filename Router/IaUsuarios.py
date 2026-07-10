from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.IaUsuarios import IaUsuarios
from Utils.decorator import http_decorator
from Config.db import get_db

ia_usuarios_router = APIRouter()


@ia_usuarios_router.post('/listar', tags=["IaUsuarios"])
@http_decorator
def listar(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return IaUsuarios(db).listar(data)


@ia_usuarios_router.post('/listar-dms', tags=["IaUsuarios"])
@http_decorator
def listar_dms(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return IaUsuarios(db).listar_dms(data)


@ia_usuarios_router.post('/crear', tags=["IaUsuarios"])
@http_decorator
def crear(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return IaUsuarios(db).crear(data)


@ia_usuarios_router.post('/actualizar', tags=["IaUsuarios"])
@http_decorator
def actualizar(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return IaUsuarios(db).actualizar(data)


@ia_usuarios_router.post('/eliminar', tags=["IaUsuarios"])
@http_decorator
def eliminar(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return IaUsuarios(db).eliminar(data)

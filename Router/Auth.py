from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Auth import Auth
from Config.db import get_db

auth_router = APIRouter()


@auth_router.post('/login', tags=["Auth"])
def login(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return Auth(db).login(data)


@auth_router.post('/me', tags=["Auth"])
def me(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    return Auth(db).me(data)

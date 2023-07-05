from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session

from ._common import auth_basic, get_db
from ..._shared import configuration as cfg
from ...davult import schemas
from ...davult.crud import token as token_db, user as user_db


router = APIRouter()


@router.get('/auth')
def auth(db: Annotated[Session, Depends(get_db)], credentials: Annotated[tuple[str, str], Depends(auth_basic)]):
    username, password = credentials

    user = user_db.find_user(db, username)

    token = token_db.generate_token(db, schemas.TokenCreate(
        owner_id=user.id,
        password=password,
        lifetime=cfg['security']['token_lifetime']
    ))

    return {'data': {'username': user.username, 'token': token.value}, 'valid': True, "error": {"title": "", "message": ""}}


@router.get('/logoff')
def logoff(db: Annotated[Session, Depends(get_db)], authorization: Annotated[str, Header()]):
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=422, detail="invalid authorization method")

    token_db.expire_token(db, token_db.find_token(db, authorization[7:]))
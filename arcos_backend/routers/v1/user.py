import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from ._common import auth_basic, auth_bearer, get_db
from ..._shared import filesystem as fs
from ..._utils import json2dict
from ...davult import schemas, models
from ...davult.crud import user as user_db


router = APIRouter()


@router.get('/create')
def user_create(db: Annotated[Session, Depends(get_db)], credentials: Annotated[tuple[str, str], Depends(auth_basic)]):
    username, password = credentials

    try:
        user = user_db.create_user(db, schemas.UserCreate(username=username, password=password))
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid username")
    except RuntimeError:
        raise HTTPException(status_code=409, detail="username already exists")
    fs.create_userspace(user.id)

    return {'error': {'valid': True}}


@router.get('/properties')
def user_properties(user: Annotated[models.User, Depends(auth_bearer)]):
    return {**json2dict(user.properties), 'valid': True, 'statusCode': 200}


@router.post('/properties/update')
async def user_properties_update(request: Request, db: Annotated[Session, Depends(get_db)], user: Annotated[models.User, Depends(auth_bearer)]):
    try:
        properties = json.JSONDecoder().decode((await request.body()).decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=422)

    user_db.update_user_properties(db, user, properties)


@router.get('/delete')
def user_delete(db: Annotated[Session, Depends(get_db)], user: Annotated[models.User, Depends(auth_bearer)]):
    user_db.delete_user(db, user)


@router.get('/rename')
def user_rename(db: Annotated[Session, Depends(get_db)], user: Annotated[models.User, Depends(auth_bearer)], newname: str):
    try:
        user_db.rename_user(db, user, newname)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid username")


@router.get('/changepswd')
def user_changepswd(db: Annotated[Session, Depends(get_db)], user: Annotated[models.User, Depends(auth_bearer)], new: str):
    user_db.set_user_password(db, user, new)

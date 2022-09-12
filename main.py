from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import crud
import models
import security
import schemas
from utils import get_db
from db import engine


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/users/me")
def read_users_me(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    user = security.get_current_user(db=db, token=token)
    return user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_username = security.get_user_by_username(user.username, db)
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/token", response_model=schemas.Token)
def login_with_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.authenticate_user(form_data.password, form_data.username, db=db)
    if not user:
        raise HTTPException(
            status_code=security.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    crud.make_user_active(db=db, username=form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/", response_model=List[schemas.User], response_model_exclude={"id"})
def read_users(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    if users is None:
        raise HTTPException(status_code=404, detail="No users registered")
    return users


@app.get("/users/{username}", response_model=schemas.User, response_model_exclude={"id"})
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/", response_model=schemas.User)
def delete_user(db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    user = security.get_current_user(db=db, token=token)
    db_user = crud.delete_user_by_id(db=db, user_id=user.id)
    return db_user


@app.post("/users/{user_id}/items/")
def create_item_for_user(
    item: schemas.ItemCreate, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)
):
    user = security.get_current_user(db=db, token=token)
    return crud.create_user_item(db=db, item=item, user_id=user.id)


@app.post("/users/{item_id}/")
def delete_item_for_user(
    item_id: int, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)
):
    user = security.get_current_user(db=db, token=token)
    item = crud.delete_user_item(db=db, item_id=item_id)
    if item is not None:
        if item.owner_id == user.id:
            db.delete(item)
            db.commit()
            return item
        else:
            return {"message": "You can delete only your items"}
    else:
        return {"message: ": "No such item"}


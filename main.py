from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import crud
import models
import security
import schemas
from db import engine, SessionLocal


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/users/me")
def read_users_me(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    user = security.get_current_user(db, token)
    return user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


@app.post("/token", response_model=schemas.Token)
def login_with_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.authenticate_user(form_data.password, form_data.username, db)
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
    crud.make_user_active(db, form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/", response_model=List[schemas.User], response_model_exclude={"id"})
def read_users(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    users = crud.get_users(db, skip, limit)
    if users is None:
        raise HTTPException(status_code=404, detail="No users registered")
    return users


@app.get("/users/{username}", response_model=schemas.User, response_model_exclude={"id"})
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = security.get_user_by_username(username, db)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}", response_model=schemas.User)
def delete_user(db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    user = security.get_current_user(db, token)
    db_user = crud.delete_current_user(db, user.id)
    return db_user


@app.post("/users/{user_id}/items/")
def create_item_for_user(
    item: schemas.ItemCreate, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)
):
    return crud.create_user_item(db, item, token)


@app.post("/items/delete/{item_id}")
def delete_item_for_user(item_id: str, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    return crud.delete_item_by_id(item_id, db, token)


@app.put("/items/update/{item_id}")
def update_item_for_user(
    item: schemas.ItemCreate, item_id: str, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)
):
    return crud.update_item(item_id, db, token, item)


@app.put("/users/admin/{user_id}")
def make_user_admin(user_id: str, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    security.set_superuser(db)
    return security.make_admin(db, token, user_id)


from sqlalchemy.orm import Session
import security
from fastapi import HTTPException
import models
import datetime
import schemas


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    users = db.query(models.User).offset(skip).limit(limit).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users registered")
    return users


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        email=user.email, hashed_password=security.get_password_hash(user.password),
        username=user.username, full_name=user.full_name, is_active=False, is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_current_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter_by(id=user_id).first()
    db.delete(db_user)
    db.commit()
    return db_user


def create_user_item(db: Session, item: schemas.ItemCreate, user_id):
    db_item = models.Item(
        **item.dict(), owner_id=user_id, created_on=datetime.datetime.now(), updated_on=datetime.datetime.now()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message: ": "Item was created successfully"}


def delete_item_by_id(item_id: int, db: Session, token: str):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    user = security.get_current_user(db, token)
    if item is not None:
        if item.owner_id == user.id:
            db.delete(item)
            db.commit()
            raise HTTPException(status_code=200, detail="Item was deleted successfully")
        else:
            raise HTTPException(status_code=404, detail="You can only delete items you own")
    else:
        raise HTTPException(status_code=404, detail="Item not found")


def make_user_active(db: Session, username: str):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user is None:
        return None
    for var, value in vars(db_user).items():
        setattr(db_user, "is_active", True) if value else None

    db_user.is_active = True
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

# TODO: Create a main superuser
# TODO: Create a function that will allow to change the is_admin state
# TODO: Create scopes that will allow admins to make whatever they want
# TODO: Create a function that will allow to update items time
# TODO: Make a dockerfile that will allow to run my app
# TODO: Read tiangolo's fullstack project code and DJWOMS code
# TODO: Read some more FastAPI documentation
# TODO: Implement routes to my app
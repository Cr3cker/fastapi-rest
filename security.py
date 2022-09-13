from fastapi.security import OAuth2PasswordBearer
import schemas
from datetime import datetime, timedelta
import models
from typing import Union
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext


SECRET_KEY = "b47e7c443994e10a789ee0fbd2e60665d2d788acc93d6beafe32819539f23732"
SUPERUSER_HASH = "$2b$12$wcNtWizHOP1pDVilZMDXm.M7/fpGrFIaQ/CCIoDMvECnLmlsXXCz2"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(password, username, db: Session):
    user = get_user_by_username(username, db)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_username(username, db: Session):
    username = db.query(models.User).filter(models.User.username == username).first()
    if username:
        return schemas.UserInDB.from_orm(username)


def get_current_user(db: Session, token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(token_data.username, db)
    if user is None:
        raise credentials_exception
    return user


def set_superuser(db: Session):
    db_user = db.query(models.User).filter(
        models.User.username == 'superuser', models.User.hashed_password == SUPERUSER_HASH).first()
    if db_user is None:
        return None
    for var, value in vars(db_user).items():
        setattr(db_user, "is_superuser", True) if value else None
        setattr(db_user, "is_admin", True) if value else None

    db_user.is_superuser = True
    db.add(db_user)
    db.commit()
    db.refresh(db_user)


def make_admin(db: Session, token: str, user_id: str):
    user_current = get_current_user(db, token)
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user and user_current.is_superuser and not db_user.is_admin:
        db_user.is_admin = True
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        raise HTTPException(status_code=200, detail=f"User {user_id} became admin!")
    else:
        raise HTTPException(status_code=404, detail="User is admin or you have no permission")


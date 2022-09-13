from typing import List, Union
import datetime
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class ItemBase(BaseModel):
    title: str
    description: str


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: str
    owner_id: str
    updated_on: datetime.datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created_on: datetime.datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    username: str
    full_name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str
    is_active: bool = False
    is_admin: bool = False
    items: List[Item] = []

    class Config:
        orm_mode = True


class UserInDB(User):
    is_superuser: bool = False
    hashed_password: str

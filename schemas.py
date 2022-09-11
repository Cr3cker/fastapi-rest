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
    description: Union[str, None] = None


class ItemCreate(ItemBase):
    created_on: datetime.datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_on: datetime.datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: Union[str, None] = None
    username: str
    full_name: Union[str, None] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: Union[bool, None] = False
    items: List[Item] = []

    class Config:
        orm_mode = True


class UserInDB(User):
    hashed_password: str




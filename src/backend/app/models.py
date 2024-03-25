from fastapi import File
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel, TIMESTAMP, JSON
from datetime import datetime
from typing import Dict, Any, Optional


# Shared properties
# TODO replace email str with EmailStr when sqlmodel supports it
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None


# Generic message
class MessageInfo(SQLModel):
    message: str


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# TODO replace email str with EmailStr when sqlmodel supports it
class UserCreateOpen(SQLModel):
    email: str
    password: str
    full_name: str | None = None


# Properties to receive via API on update, all are optional
# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdate(UserBase):
    email: str | None = None
    password: str | None = None


# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdateMe(SQLModel):
    full_name: str | None = None
    email: str | None = None


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner")
    templates: list["Template"] = Relationship(back_populates="owner")


# Properties to return via API, id is always required
class UserOut(UserBase):
    id: int


class UsersOut(SQLModel):
    data: list[UserOut]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str
    description: str | None = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = None


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemOut(ItemBase):
    id: int
    owner_id: int


class ItemsOut(SQLModel):
    data: list[ItemOut]
    count: int


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: int | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str


#new code
class Template(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="templates")
    private: bool = Field(nullable=False)
    prompt: str = Field(nullable=False)


class TemplateCreate(SQLModel):
    title: str
    prompt: str
    private: Optional[bool]


class TemplateOut(SQLModel):
    id: int
    title: str
    prompt: str
    private: bool


class TemplatesOut(SQLModel):
    count: int
    templates: list[TemplateOut]


class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    template_id: int | None
    messages: list["Message"] = Relationship(back_populates="chat")
    is_complete: bool = Field(default=False, nullable=False)
    history: Dict[Any, Any] | None = Field(default={"messages": []}, sa_column=Column(JSON))


class ChatOut(SQLModel):
    id: int
    template_id: int
    is_complete: bool
    messages: list["Message"]
    history: Dict[Any,Any]


class ChatCreate(SQLModel):
    template_id: int


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id", nullable=False)
    chat: Chat = Relationship(back_populates="messages")
    body: str = Field(nullable=False)
    data: datetime = Field(default=datetime.utcnow())


class CreateMessage(SQLModel):
    chat_id: int
    body: Optional[str]

class HistoryUpdate(SQLModel):
    history: Dict[Any, Any]

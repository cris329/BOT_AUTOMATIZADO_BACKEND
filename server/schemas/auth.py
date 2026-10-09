"""
Esquemas de login y perfil de la app.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(default="", max_length=120)
    rol: str = Field(default="FORMACION COMPLEMENTARIA", max_length=80)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str

    model_config = {"from_attributes": True}

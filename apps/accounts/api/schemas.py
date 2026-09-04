from ninja import Schema
from pydantic import EmailStr
from typing import Optional


class ApiTokenOut(Schema):
    api_token: str


class UserOut(Schema):
    id: int
    username: str
    email: EmailStr | str
    full_name: str
    role: str
    phone: str
    crp: str
    specialty: str
    is_active: bool
    is_active_clinical: bool
    two_factor_enabled: bool = False


class MeOut(Schema):
    id: int
    username: str
    email: EmailStr | str
    full_name: str
    role: str
    is_superuser: bool
    is_staff: bool
    is_active: bool
    two_factor_enabled: bool = False


class CreateUserIn(Schema):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = ""
    role: str = "assistant"
    phone: Optional[str] = ""
    crp: Optional[str] = ""
    specialty: Optional[str] = ""
    is_active: bool = True
    is_active_clinical: bool = True


class UpdateUserIn(Schema):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    crp: Optional[str] = None
    specialty: Optional[str] = None
    is_active: Optional[bool] = None
    is_active_clinical: Optional[bool] = None
    password: Optional[str] = None


class MessageOut(Schema):
    message: str


class LoginIn(Schema):
    email: str
    password: str


class LoginOut(Schema):
    access: Optional[str] = None
    user: Optional[dict] = None


class ForgotPasswordIn(Schema):
    email: EmailStr


class ResetPasswordConfirmIn(Schema):
    uid: str
    token: str
    password: str


class RegisterIn(Schema):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "assistant"
    phone: Optional[str] = ""
    crp: Optional[str] = ""
    specialty: Optional[str] = ""


class RegisterOut(Schema):
    success: bool
    message: str
    user: Optional[UserOut] = None

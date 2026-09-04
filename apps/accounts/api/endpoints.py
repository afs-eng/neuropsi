from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.conf import settings
import logging
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from apps.api.auth import bearer_auth
from apps.common.security import rate_limit
from apps.audit.services import AuditService


from apps.accounts.models import User
from apps.accounts.permissions import can_manage_users, can_view_users
from apps.accounts.selectors import get_active_users
from apps.accounts.services import (
    create_user,
    update_user,
    issue_api_token,
    regenerate_api_token,
)

from .schemas import (
    ApiTokenOut,
    UserOut,
    MeOut,
    CreateUserIn,
    UpdateUserIn,
    MessageOut,
    LoginIn,
    LoginOut,
    ForgotPasswordIn,
    ResetPasswordConfirmIn,
    RegisterIn,
    RegisterOut,
)


router = Router(tags=["accounts"])
logger = logging.getLogger(__name__)


@router.post("/login", response={200: LoginOut, 429: MessageOut})
def login(request, payload: LoginIn):
    try:
        rate_limit(request, "accounts-login", limit=5, window_seconds=900)

        email = payload.email
        if not email:
            raise HttpError(400, "Informe o email")

        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            user = User.objects.get(email=email)
            user = authenticate(username=user.username, password=payload.password)
        except User.DoesNotExist:
            user = None

        if not user:
            AuditService.log(
                request, "login_failed", "account", metadata={"email": email}
            )
            raise HttpError(401, "Credenciais inválidas")
        if not user.is_active:
            AuditService.log(
                request, "login_blocked", "account", resource_id=str(user.id)
            )
            raise HttpError(403, "Usuário inativo")
        access = issue_api_token(user)
        AuditService.log(request, "login", "account", resource_id=str(user.id))
        return {
            "access": access,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name or user.get_full_name() or user.username,
                "display_name": user.display_name,
                "role": user.role,
                "sex": user.sex,
                "specialty": user.specialty,
                "two_factor_enabled": user.two_factor_enabled,
            },
        }

    except Exception as e:
        logger.exception("Erro crítico no login")
        raise e


@router.post(
    "/register",
    response={201: RegisterOut, 400: MessageOut, 403: MessageOut, 429: MessageOut},
)
def register(request, payload: RegisterIn):
    rate_limit(request, "accounts-register", limit=3, window_seconds=900)

    if not settings.ENABLE_PUBLIC_REGISTRATION:
        return 403, {"message": "Cadastro público desativado."}

    if User.objects.filter(email=payload.email).exists():
        return 400, {"message": "Email já cadastrado."}
    if User.objects.filter(username=payload.username).exists():
        return 400, {"message": "Nome de usuário já em uso."}

    if payload.crp and User.objects.filter(crp=payload.crp).exists():
        return 400, {"message": "CRP já vinculado a outro profissional."}

    user = create_user(**payload.dict())
    AuditService.track_create(
        request,
        "account",
        str(user.id),
        {"username": user.username, "role": user.role},
    )

    return 201, {
        "success": True,
        "message": "Usuário criado com sucesso.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.display_name,
            "role": user.role,
            "phone": user.phone,
            "crp": user.crp,
            "specialty": user.specialty,
            "is_active": user.is_active,
            "is_active_clinical": user.is_active_clinical,
            "two_factor_enabled": user.two_factor_enabled,
        },
    }


@router.post("/forgot-password", response={200: MessageOut, 429: MessageOut})
def forgot_password(request, payload: ForgotPasswordIn):
    rate_limit(request, "accounts-forgot-password", limit=5, window_seconds=900)

    user = User.objects.filter(email=payload.email, is_active=True).first()

    if user:
        AuditService.log(
            request, "password_reset_requested", "account", resource_id=str(user.id)
        )
        from django.core.mail import send_mail

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = (
            f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')}"
            f"/reset-password?uid={uid}&token={token}"
        )

        send_mail(
            subject="Redefinicao de senha - NeuroAvalia",
            message=(
                "Ola!\n\n"
                "Recebemos uma solicitacao para redefinir sua senha no NeuroAvalia.\n"
                f"Use este link para cadastrar uma nova senha:\n{reset_url}\n\n"
                "Se voce nao fez esta solicitacao, ignore este e-mail."
            ),
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "no-reply@neuroavalia.local"
            ),
            recipient_list=[user.email],
            fail_silently=False,
        )

    return {
        "message": "Se o email estiver cadastrado, enviaremos as instrucoes para redefinir sua senha."
    }


@router.post("/reset-password/confirm", response={200: MessageOut, 400: MessageOut})
def reset_password_confirm(request, payload: ResetPasswordConfirmIn):
    try:
        user_id = urlsafe_base64_decode(payload.uid).decode()
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):
        return 400, {"message": "Link invalido ou expirado."}

    if not default_token_generator.check_token(user, payload.token):
        return 400, {"message": "Link invalido ou expirado."}

    user.set_password(payload.password)
    user.save(update_fields=["password"])
    AuditService.log(
        request, "password_reset_confirmed", "account", resource_id=str(user.id)
    )

    return {"message": "Senha redefinida com sucesso."}


@router.get("/me", response=MeOut, auth=django_auth)
def me(request):
    user = request.user
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.display_name,
        "role": user.role,
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
    }


@router.get("/users", response=list[UserOut], auth=django_auth)
def list_users(request):
    if not can_view_users(request):
        raise HttpError(403, "Você não tem permissão para listar usuários.")

    users = get_active_users()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.display_name,
            "role": user.role,
            "phone": user.phone,
            "crp": user.crp,
            "specialty": user.specialty,
            "is_active": user.is_active,
            "is_active_clinical": user.is_active_clinical,
            "two_factor_enabled": user.two_factor_enabled,
        }
        for user in users
    ]


@router.post("/users", response={201: UserOut, 403: MessageOut}, auth=django_auth)
def create_user_endpoint(request, payload: CreateUserIn):
    if not can_manage_users(request):
        return 403, {"message": "Você não tem permissão para criar usuários."}

    user = create_user(**payload.dict())
    AuditService.track_create(
        request,
        "account",
        str(user.id),
        {"username": user.username, "role": user.role},
    )

    return 201, {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.display_name,
        "role": user.role,
        "phone": user.phone,
        "crp": user.crp,
        "specialty": user.specialty,
        "is_active": user.is_active,
        "is_active_clinical": user.is_active_clinical,
        "two_factor_enabled": user.two_factor_enabled,
    }


@router.patch(
    "/users/{user_id}", response={200: UserOut, 403: MessageOut}, auth=django_auth
)
def update_user_endpoint(request, user_id: int, payload: UpdateUserIn):
    if not can_manage_users(request):
        return 403, {"message": "Você não tem permissão para editar usuários."}

    user = get_object_or_404(User, id=user_id)
    cleaned_data = payload.dict(exclude_unset=True)
    user = update_user(user, **cleaned_data)
    AuditService.track_update(
        request,
        "account",
        str(user.id),
        {},
        cleaned_data,
    )

    return 200, {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.display_name,
        "role": user.role,
        "phone": user.phone,
        "crp": user.crp,
        "specialty": user.specialty,
        "is_active": user.is_active,
        "is_active_clinical": user.is_active_clinical,
        "two_factor_enabled": user.two_factor_enabled,
    }


@router.get("/token", response={410: MessageOut}, auth=bearer_auth)
def get_api_token(request):
    return 410, {"message": "Token não é recuperável. Use login ou gere um novo token."}


@router.post("/token/regenerate", response=ApiTokenOut, auth=bearer_auth)
def regenerate_token_endpoint(request):
    rate_limit(request, "accounts-token-regenerate", limit=10, window_seconds=900)

    token = regenerate_api_token(request.auth)
    AuditService.log(
        request, "token_regenerated", "account", resource_id=str(request.auth.id)
    )
    return {"api_token": token}

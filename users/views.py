from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from drf_spectacular.utils import extend_schema, OpenApiExample
from skilltime.api.schema_serializers import ErrorResponseSerializer

from .models import User, RefreshToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, RefreshSerializer,
    LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, MeSerializer
)
from .utils import (
    make_access_token, make_refresh_token,
    make_password_reset_token, verify_reset_token
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register",
        request=RegisterSerializer,
        responses={201: None, 400: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = make_refresh_token()
        RefreshToken.objects.create(
            user=user,
            token=refresh,
            expires_at=timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        )

        return Response(
            {"access_token": make_access_token(user), "refresh_token": refresh},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"  

    @extend_schema(
        tags=["Auth"],
        summary="Login",
        request=LoginSerializer,
        responses={200: None, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if (
            not user
            or not user.is_active
            or not user.check_password(serializer.validated_data["password"])
        ):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = make_refresh_token()
        RefreshToken.objects.create(
            user=user,
            token=refresh,
            expires_at=timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        )

        return Response({"access_token": make_access_token(user), "refresh_token": refresh})


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Refresh access token",
        request=RefreshSerializer,
        responses={200: None, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer},
    )
    @transaction.atomic
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["refresh_token"]
        rtoken = get_object_or_404(RefreshToken.objects.select_for_update(), token=token)

        if not rtoken.is_valid():
            return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        rtoken.revoked = True
        rtoken.save()

        new_refresh = make_refresh_token()
        RefreshToken.objects.create(
            user=rtoken.user,
            token=new_refresh,
            expires_at=timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        )

        return Response({"access_token": make_access_token(rtoken.user), "refresh_token": new_refresh})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Logout (revoke refresh token)",
        request=LogoutSerializer,
        responses={200: None, 400: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        RefreshToken.objects.filter(
            token=serializer.validated_data["refresh_token"],
            user=request.user,
        ).update(revoked=True)

        return Response({"detail": "Logged out"})


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "forgot"  

    @extend_schema(
        tags=["Auth"],
        summary="Request password reset",
        request=ForgotPasswordSerializer,
        responses={200: None, 400: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if not user:
            return Response({"detail": "If email exists, link sent"})

        token = make_password_reset_token(user)
        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + settings.JWT_RESET_TOKEN_LIFETIME,
        )

        send_mail(
            "Reset password",
            f"{settings.FRONTEND_URL}/reset-password?token={token}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

        return Response({"detail": "If email exists, link sent"})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Reset password",
        request=ResetPasswordSerializer,
        responses={200: None, 400: ErrorResponseSerializer},
    )
    @transaction.atomic
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = verify_reset_token(serializer.validated_data["token"])
        if not payload:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        prt = get_object_or_404(
            PasswordResetToken.objects.select_for_update(),
            token=serializer.validated_data["token"],
            used=False,
        )

        if not prt.is_valid():
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

        user = prt.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        RefreshToken.objects.filter(user=user).update(revoked=True)
        prt.used = True
        prt.save()

        return Response({"detail": "Password reset successful"})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get current user (/me)",
        responses={200: MeSerializer, 401: ErrorResponseSerializer},
    )
    @extend_schema(tags=["Audit"], summary="Get audit log detail (admin)")
    def get(self, request):
        return Response({"id": request.user.id, "email": request.user.email, "role": request.user.role})
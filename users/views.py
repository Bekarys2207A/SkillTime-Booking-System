from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from .models import User, RefreshToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, RefreshSerializer,
    LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from .utils import (
    make_access_token, make_refresh_token,
    make_password_reset_token, verify_reset_token
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

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

        return Response({
            "access_token": make_access_token(user),
            "refresh_token": refresh,
        }, status=201)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if not user or not user.check_password(serializer.validated_data["password"]):
            return Response({"detail": "Invalid credentials"}, status=401)

        refresh = make_refresh_token()
        RefreshToken.objects.create(
            user=user,
            token=refresh,
            expires_at=timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        )

        return Response({
            "access_token": make_access_token(user),
            "refresh_token": refresh,
        })


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["refresh_token"]
        rtoken = get_object_or_404(RefreshToken.objects.select_for_update(), token=token)

        if not rtoken.is_valid():
            return Response({"detail": "Invalid token"}, status=401)

        rtoken.revoked = True
        rtoken.save()

        new_refresh = make_refresh_token()
        RefreshToken.objects.create(
            user=rtoken.user,
            token=new_refresh,
            expires_at=timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        )

        return Response({
            "access_token": make_access_token(rtoken.user),
            "refresh_token": new_refresh,
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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

    @transaction.atomic
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = verify_reset_token(serializer.validated_data["token"])
        if not payload:
            return Response({"detail": "Invalid token"}, status=400)

        prt = get_object_or_404(
            PasswordResetToken,
            token=serializer.validated_data["token"],
            used=False,
        )

        user = prt.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        RefreshToken.objects.filter(user=user).update(revoked=True)
        prt.used = True
        prt.save()

        return Response({"detail": "Password reset successful"})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "email": request.user.email,
            "role": request.user.role,
        })
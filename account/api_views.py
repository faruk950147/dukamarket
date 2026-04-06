from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from account.serializers import (
    SignupSerializer,
    OTPVerifySerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    ProfileSerializer,
    ResendOTPSerializer,
)

# =========================
# Signup
# =========================
class SignupView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Signup successful. Check email for OTP"}, status=201)
        return Response(serializer.errors, status=400)


# =========================
# OTP Verify
# =========================
class OTPVerifyView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"],
            })
        return Response(serializer.errors, status=400)


# =========================
# Login
# =========================
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=400)


# =========================
# Logout
# =========================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Logout successful"})
        return Response(serializer.errors, status=400)


# =========================
# Profile
# =========================
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated"})
        return Response(serializer.errors, status=400)


# =========================
# Change Password
# =========================
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=400)


# =========================
# Password Reset Request
# =========================
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "If email exists, OTP sent"})
        return Response(serializer.errors, status=400)


# =========================
# Password Reset Verify
# =========================
class PasswordResetVerifyView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successful"})
        return Response(serializer.errors, status=400)
    
    
# =========================
# Resend OTP
# =========================
class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "OTP resent"})
        return Response(serializer.errors, status=400)
    

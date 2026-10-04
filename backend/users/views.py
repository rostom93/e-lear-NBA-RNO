from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .permissions import IsAdminRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserMeUpdateSerializer,
    UserSerializer,
)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserMeUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class UserAdminViewSet(viewsets.ModelViewSet):
    """Admin-only CRUD for platform users."""

    queryset = CustomUser.objects.all().order_by("email")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminRole]

    @action(detail=True, methods=["post"])
    def set_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get("role")
        if role not in CustomUser.Role.values:
            return Response(
                {"detail": f"Invalid role. Choose one of {list(CustomUser.Role.values)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.role = role
        if role == CustomUser.Role.ADMIN:
            user.is_staff = True
        user.save(update_fields=["role", "is_staff"])
        return Response(UserAdminSerializer(user).data)

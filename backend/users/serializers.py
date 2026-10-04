from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login with email; response includes user payload."""

    username_field = CustomUser.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "credit_balance",
            "is_active",
            "date_joined",
        )
        read_only_fields = ("id", "credit_balance", "date_joined")


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "credit_balance",
            "is_active",
            "is_staff",
            "date_joined",
            "password",
        )
        read_only_fields = ("id", "date_joined")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "Password is required."})
        if not validated_data.get("username"):
            validated_data["username"] = validated_data["email"]
        if validated_data.get("role") == CustomUser.Role.ADMIN:
            validated_data["is_staff"] = True
        return CustomUser.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if "username" in validated_data and not validated_data["username"]:
            validated_data["username"] = validated_data.get("email", instance.email)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if instance.role == CustomUser.Role.ADMIN:
            instance.is_staff = True
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ("email", "password", "first_name", "last_name", "username")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        if not validated_data.get("username"):
            validated_data["username"] = validated_data["email"]
        return CustomUser.objects.create_user(
            role=CustomUser.Role.STUDENT,
            credit_balance=0,
            **validated_data,
        )


class UserMeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "username")

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "is_staff", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        norm_email = value.strip().lower()
        if User.objects.filter(email__iexact=norm_email).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return norm_email

    def validate_username(self, value):
        norm_username = value.strip()
        if User.objects.filter(username__iexact=norm_username).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return norm_username

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")

        if not email:
            raise serializers.ValidationError(
                {"error": "Must include email."}
            )

        # Allow login using email in username field or email field
        user = None
        try:
            user_obj = User.objects.get(email__iexact=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if not user:
            raise serializers.ValidationError(
                {"error": "Unable to log in with provided credentials."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"error": "User account is disabled."}
            )

        attrs["user"] = user
        return attrs


class AuthResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    access = serializers.CharField(required=False)
    refresh = serializers.CharField(required=False)


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class LogoutResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

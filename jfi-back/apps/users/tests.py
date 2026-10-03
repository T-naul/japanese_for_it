from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPassword123!",
            first_name="Test",
            last_name="User",
        )

    def test_register_success(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "first_name": "New",
            "last_name": "Person",
        }
        res = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertIn("user", res.data)
        self.assertEqual(res.data["user"]["username"], "newuser")
        self.assertEqual(res.data["user"]["email"], "newuser@example.com")

    def test_register_duplicate_username(self):
        data = {
            "username": "testuser",
            "email": "unique@example.com",
            "password": "StrongPassword123!",
        }
        res = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", res.data)

    def test_register_duplicate_email(self):
        data = {
            "username": "differentuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
        }
        res = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)

    def test_login_missing_email(self):
        res = self.client.post(
            "/api/auth/login/",
            {"password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    def test_login_with_email(self):
        res = self.client.post(
            "/api/auth/login/",
            {"email": "testuser@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.data["user"]["username"], "testuser")

    def test_login_invalid_password(self):
        res = self.client.post(
            "/api/auth/login/",
            {"email": "testuser@example.com", "password": "WrongPassword!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    def test_login_nonexistent_user(self):
        res = self.client.post(
            "/api/auth/login/",
            {"email": "ghost@example.com", "password": "SomePassword123!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        res = self.client.post(
            "/api/auth/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_token_verify(self):
        refresh = RefreshToken.for_user(self.user)
        res = self.client.post(
            "/api/auth/verify/",
            {"token": str(refresh.access_token)},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_me_authenticated_jwt_bearer(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "testuser")
        self.assertEqual(res.data["email"], "testuser@example.com")

    def test_me_unauthenticated(self):
        res = self.client.get("/api/auth/me/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_logout_success(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        res = self.client.post(
            "/api/auth/logout/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["detail"], "Successfully logged out.")

    def test_logout_missing_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        res = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Refresh token is required.", res.data["detail"])

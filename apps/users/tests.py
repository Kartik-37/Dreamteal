"""
Backend tests for apps.users.
Tests UserProfile model, automatic signal profile creation, and standard Django auth.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.users.models import UserProfile

User = get_user_model()


class UsersModelsTestCase(TestCase):
    def test_user_profile_signal_creation(self):
        """Verifies that creating a standard Django User automatically provisions a UserProfile."""
        user = User.objects.create_user(username='diana', email='diana@example.com', password='secretpassword')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(user.profile.display_name, 'diana')

    def test_user_authentication_no_hardcoded_named_user(self):
        """Verifies arbitrary standard users can be authenticated without hardcoded user constraints."""
        for name in ['alpha_user', 'beta_user', 'gamma_user']:
            u = User.objects.create_user(username=name, password='safe_password')
            self.assertTrue(u.check_password('safe_password'))
            self.assertEqual(u.profile.user, u)


from rest_framework.test import APIClient


class UsersAuthAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='auth_tester',
            email='auth@dreamteal.local',
            password='auth_password123'
        )

    def test_csrf_token_endpoint(self):
        res = self.client.get('/api/v1/users/csrf/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('csrftoken', res.data)
        self.assertTrue(len(res.data['csrftoken']) > 10)

    def test_session_login_me_and_logout_flow(self):
        # 1. Login with correct credentials
        res_login = self.client.post('/api/v1/users/login/', {
            'username': 'auth_tester',
            'password': 'auth_password123'
        })
        self.assertEqual(res_login.status_code, 200)
        self.assertEqual(res_login.data['user']['username'], 'auth_tester')

        # 2. Get authenticated profile via /api/v1/users/me/
        res_me = self.client.get('/api/v1/users/me/')
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.data['username'], 'auth_tester')
        self.assertEqual(res_me.data['display_name'], 'auth_tester')

        # 3. Update profile via PATCH /api/v1/users/me/
        res_patch = self.client.patch('/api/v1/users/me/', {
            'display_name': 'PopCulturePro',
            'bio': 'Film and indie game enthusiast.'
        })
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['display_name'], 'PopCulturePro')
        self.assertEqual(res_patch.data['bio'], 'Film and indie game enthusiast.')

        # 4. Logout
        res_logout = self.client.post('/api/v1/users/logout/')
        self.assertEqual(res_logout.status_code, 200)

        # 5. Subsequent /api/v1/users/me/ is 401/403 Unauthorized
        res_unauth = self.client.get('/api/v1/users/me/')
        self.assertIn(res_unauth.status_code, [401, 403])


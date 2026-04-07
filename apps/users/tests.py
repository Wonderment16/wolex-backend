from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from unittest.mock import patch
from django.test import override_settings               # added import
    
User = get_user_model()

def create_user(email="test@example.com", password="ComplexPass123!", **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


class AuthTests(APITestCase):
    def setUp(self):
        self.good_password = 'ComplexPass123!'                 # reuseable strong password

    def test_register_success(self):
        url = reverse('register')
        data = {
            'first_name': 'Alice', 
            'email': 'alice@example.com', 
            'password': 'ComplexPass123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], 'alice@example.com')
        self.assertFalse(response.data['user']['profile_completed'])
        self.assertFalse(response.data['user']['email_verified'])
        # registration should trigger a verification email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verify-email', mail.outbox[0].body)

    def test_register_duplicate_email(self):
        create_user(email='bob@example.com')
        url = reverse('register')
        data = {
            'first_name': 'Bob', 
            'email': 'bob@example.com', 
            'password': self.good_password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('message', response.data)
        self.assertIn('email', response.data['message'])

    def test_password_validator_reject(self):
        url = reverse('register')
        data = {
            'first_name': 'Eve', 
            'email': 'eve@example.com', 
            'password': 'short'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.data)
        self.assertTrue(
            "password" in response.data["message"] or
            "non_field_errors" in response.data["message"]
        )
    def test_login_returns_tokens_and_profile_flag(self):
        # login existing user
        user = create_user(email='login@example.com', password='Password1!')
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {'email': user.email, 'password': 'Password1!'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertIn('user', resp.data)
        self.assertIn('profile_completed', resp.data['user'])

    def test_profile_patch(self):
        user = create_user(email='charlie@example.com')
        self.client.force_authenticate(user=user)
        url = reverse('profile')
        patch_data = {
            'last_name': 'Brown',
            'account_type': 'BUSINESS',
            'nationality': 'United States'
        }
        resp = self.client.patch(url, patch_data, format='multipart')
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.last_name, 'Brown')
        self.assertTrue(user.profile.nationality == 'United States')
        # settings should be auto-updated
        self.assertEqual(user.settings.currency, 'USD')
        # response contains message, user, profile, settings
        self.assertIn('message', resp.data)
        self.assertIn('user', resp.data)
        self.assertIn('profile', resp.data)
        self.assertIn('settings', resp.data)

    def test_password_reset_request_generic(self):
        url = reverse('password_reset_request')
        resp = self.client.post(url, {'email': 'noone@example.com'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.data)

    def test_password_reset_confirm(self):
        user = create_user(email='dave@example.com')
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = reverse('password_reset_confirm')
        resp = self.client.post(url, {'uid': uid, 'token': token, 'new_password': 'Newpass1!'}, format='json')
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('Newpass1!'))


    @override_settings(GOOGLE_CLIENT_ID="test-google-client-id")
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_new_user(self, mock_verify):
        # simulate google returning data
        mock_verify.return_value = {
            'email': 'guser@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'email_verified': True,
        }
        url = reverse('google_auth')
        resp = self.client.post(url, {'token': 'dummy'}, format='json')
        print("GOOGLE AUTH RESPONSE:", resp.status_code, resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['is_new_user'])
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    @override_settings(GOOGLE_CLIENT_ID="test-google-client-id")
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_existing_user(self, mock_verify):
        create_user(email='gexist@example.com')
        mock_verify.return_value = {
            'email': 'gexist@example.com',
            'given_name': 'G',
            'family_name': 'Exist',
            'email_verified': True,
        }
        url = reverse('google_auth')
        resp = self.client.post(url, {'token': 'dummy'}, format='json')
        print("GOOGLE AUTH RESPONSE:", resp.status_code, resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['is_new_user'])

    def test_email_verification_flow(self):
        user = create_user(email='verify@example.com')
        # request
        url = reverse('email_verify_request')
        resp = self.client.post(url, {'email': user.email}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.data)
        # simulate token generation
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url2 = reverse('email_verify_confirm')
        resp2 = self.client.post(url2, {'uid': uid, 'token': token}, format='json')
        self.assertEqual(resp2.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

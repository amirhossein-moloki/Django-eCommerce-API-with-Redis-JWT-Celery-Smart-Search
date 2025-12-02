from django.test import SimpleTestCase
from django.urls import reverse, resolve
from account import views


class AccountUrlsTest(SimpleTestCase):

    def test_jwt_refresh_url_resolves(self):
        url = reverse('auth:jwt-refresh')
        self.assertEqual(resolve(url).func.view_class, views.TokenRefreshView)

    def test_jwt_verify_url_resolves(self):
        url = reverse('auth:jwt-verify')
        self.assertEqual(resolve(url).func.view_class, views.TokenVerifyView)

    def test_jwt_destroy_url_resolves(self):
        url = reverse('auth:jwt-destroy')
        self.assertEqual(resolve(url).func.view_class, views.TokenDestroyView)

    def test_current_user_url_resolves(self):
        url = reverse('auth:current_user')
        self.assertEqual(resolve(url).func.cls, views.UserViewSet)

    def test_staff_check_url_resolves(self):
        url = reverse('auth:staff_check')
        self.assertEqual(resolve(url).func.cls, views.UserViewSet)

    def test_request_otp_url_resolves(self):
        url = reverse('auth:request-otp')
        self.assertEqual(resolve(url).func.view_class, views.RequestOTP)

    def test_verify_otp_url_resolves(self):
        url = reverse('auth:verify-otp')
        self.assertEqual(resolve(url).func.view_class, views.VerifyOTP)

    def test_complete_profile_url_resolves(self):
        url = reverse('auth:complete-profile')
        self.assertEqual(resolve(url).func.view_class, views.CompleteProfileView)

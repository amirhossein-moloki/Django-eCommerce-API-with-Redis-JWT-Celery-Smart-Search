from unittest.mock import patch, MagicMock
from django.test import TestCase
from .providers import SmsIrProvider, SmsProviderError
import requests


class SmsProviderTests(TestCase):
    def setUp(self):
        # Patch settings to avoid dependency on actual Django settings
        with patch("sms.providers.settings") as mock_settings:
            mock_settings.SMS_IR_API_KEY = "test_api_key"
            mock_settings.SMS_IR_LINE_NUMBER = "1234567890"
            self.provider = SmsIrProvider()

    def test_phone_number_normalization(self):
        """Tests if various phone number formats are correctly normalized."""
        self.assertEqual(self.provider._normalize_phone("+989123456789"), "09123456789")
        self.assertEqual(self.provider._normalize_phone("989123456789"), "09123456789")
        self.assertEqual(self.provider._normalize_phone("9123456789"), "09123456789")
        self.assertEqual(self.provider._normalize_phone("09123456789"), "09123456789")

    def test_invalid_phone_number_raises_error(self):
        """Tests if invalid phone numbers raise SmsProviderError."""
        with self.assertRaises(SmsProviderError):
            self.provider._normalize_phone("123")  # Too short
        with self.assertRaises(SmsProviderError):
            self.provider._normalize_phone("0912345678")  # Too short
        with self.assertRaises(SmsProviderError):
            self.provider._normalize_phone("091234567890")  # Too long
        with self.assertRaises(SmsProviderError):
            self.provider._normalize_phone("08123456789")  # Invalid prefix
        with self.assertRaises(SmsProviderError):
            self.provider._normalize_phone("not-a-number")

    @patch("sms.providers.requests.post")
    def test_send_otp_success(self, mock_post):
        """Tests successful OTP sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 1,
            "message": "موفق",
            "data": {"messageId": 12345, "cost": 1.0},
        }
        mock_post.return_value = mock_response

        response = self.provider.send_otp("09123456789", "12345", 101)
        self.assertEqual(response["messageId"], 12345)
        # Check if the number was normalized before sending
        sent_data = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_data["mobile"], "09123456789")

    @patch("sms.providers.requests.post")
    def test_send_otp_api_error(self, mock_post):
        """Tests API error during OTP sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 113,
            "message": "قالب یافت نشد",
            "data": None,
        }
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(SmsProviderError, "قالب یافت نشد") as cm:
            self.provider.send_otp("09123456789", "12345", 999)
        self.assertEqual(cm.exception.status_code, 113)

    @patch("sms.providers.requests.post")
    def test_send_text_success(self, mock_post):
        """Tests successful text message sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 1,
            "message": "موفق",
            "data": {
                "packId": "some-uuid",
                "messageIds": [12345],
                "cost": 1.0,
            },
        }
        mock_post.return_value = mock_response

        response = self.provider.send_text("09123456789", "Hello World")
        self.assertEqual(response["packId"], "some-uuid")

    @patch("sms.providers.requests.post")
    def test_network_error_raises_sms_provider_error(self, mock_post):
        """Tests if a network error is wrapped in SmsProviderError."""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaisesRegex(SmsProviderError, "Network error"):
            self.provider.send_otp("09123456789", "12345", 101)

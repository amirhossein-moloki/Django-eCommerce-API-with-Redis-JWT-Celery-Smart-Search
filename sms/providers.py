import requests
from abc import ABC, abstractmethod
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SmsProviderError(Exception):
    """Custom exception for SMS provider errors."""

    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(message)


class SmsProvider(ABC):
    @abstractmethod
    def send_otp(self, phone, code, template_id):
        pass

    @abstractmethod
    def send_text(self, phone, message):
        pass


class SmsIrProvider(SmsProvider):
    def __init__(self):
        self.api_key = getattr(settings, "SMS_IR_API_KEY", None)
        self.line_number = getattr(settings, "SMS_IR_LINE_NUMBER", None)
        self.api_url = "https://api.sms.ir/v1"

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalizes a phone number to the 09xxxxxxxxx format and validates it.
        Raises SmsProviderError if the number is invalid.
        """
        if not isinstance(phone, str):
            raise SmsProviderError(f"Invalid phone number type: {type(phone)}")

        phone = phone.strip()
        if phone.startswith("+98"):
            phone = "0" + phone[3:]
        elif phone.startswith("98"):
            phone = "0" + phone[2:]

        if len(phone) == 10 and phone.startswith("9"):
            phone = "0" + phone

        if not (len(phone) == 11 and phone.startswith("09") and phone.isdigit()):
            raise SmsProviderError(f"Invalid mobile number format: {phone}")

        return phone

    def _get_headers(self):
        if not self.api_key:
            raise SmsProviderError("SMS.ir API key is not configured.")
        return {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
        }

    def send_otp(self, phone, code, template_id):
        normalized_phone = self._normalize_phone(phone)
        headers = self._get_headers()
        headers["Accept"] = "text/plain"
        data = {
            "mobile": normalized_phone,
            "templateId": template_id,
            "parameters": [
                {"name": "CODE", "value": str(code)},
            ],
        }
        # Securely log parameters without exposing sensitive values
        log_params = [p["name"] for p in data["parameters"]]
        logger.info(
            f"Sending OTP to {normalized_phone} via sms.ir with template {template_id} "
            f"and parameters: {log_params}"
        )
        try:
            response = requests.post(
                f"{self.api_url}/send/verify", json=data, headers=headers, timeout=10
            )
            response.raise_for_status()
            response_data = response.json()

            if response_data.get("status") != 1:
                logger.error(
                    f"sms.ir OTP error for {normalized_phone}: "
                    f"status={response_data.get('status')}, "
                    f"message={response_data.get('message')}"
                )
                raise SmsProviderError(
                    response_data.get("message"), response_data.get("status")
                )

            logger.info(f"Successfully sent OTP to {normalized_phone} via sms.ir")
            return response_data.get("data")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending OTP to {normalized_phone} via sms.ir: {e}")
            raise SmsProviderError(f"Network error: {e}") from e

    def send_text(self, phone, message):
        normalized_phone = self._normalize_phone(phone)
        if not self.line_number:
            raise SmsProviderError("SMS.ir line number is not configured.")
        data = {
            "lineNumber": self.line_number,
            "messageText": message,
            "mobiles": [normalized_phone],
        }
        logger.info(f"Sending text message to {normalized_phone} via sms.ir")
        try:
            response = requests.post(
                f"{self.api_url}/send/bulk",
                json=data,
                headers=self._get_headers(),
                timeout=10,
            )
            response.raise_for_status()
            response_data = response.json()

            if response_data.get("status") != 1:
                logger.error(
                    f"sms.ir text message error for {phone}: "
                    f"status={response_data.get('status')}, "
                    f"message={response_data.get('message')}"
                )
                raise SmsProviderError(
                    response_data.get("message"), response_data.get("status")
                )

            logger.info(f"Successfully sent text message to {phone} via sms.ir")
            return response_data.get("data")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending text message to {phone} via sms.ir: {e}")
            raise SmsProviderError(f"Network error: {e}") from e

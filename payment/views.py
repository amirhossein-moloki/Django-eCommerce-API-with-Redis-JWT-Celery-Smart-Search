from logging import getLogger

from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ecommerce_api.core.api_standard_response import ApiResponse
from orders.models import Order
from . import services
import hmac
from .tasks import process_successful_payment
from ecommerce_api.core.utils import get_client_ip
from django.conf import settings
from rest_framework.permissions import AllowAny

logger = getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        operation_id="payment_process",
        description="Create a Zibal payment request for an order. Expects an order_id in request data.",
        tags=["Payments"],
        responses={
            201: OpenApiResponse(description="Zibal payment URL created successfully."),
            400: OpenApiResponse(description="Order ID is missing or invalid request data.")
        },
    )
)
class PaymentProcessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        if not order_id:
            return ApiResponse.error(
                message="Order ID is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            payment_url = services.process_payment(request, order_id)
            return ApiResponse.success(
                data={"payment_url": payment_url},
                status_code=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return ApiResponse.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


from .gateways import ZibalGatewayError


@extend_schema_view(
    get=extend_schema(
        operation_id="payment_callback_and_verify",
        description="Handles the callback from Zibal after a payment attempt and performs server-side verification.",
        tags=["Payments"],
        responses={
            200: OpenApiResponse(description="Payment verified successfully."),
            400: OpenApiResponse(description="Invalid callback request or verification failed."),
            404: OpenApiResponse(description="Order not found for the given trackId."),
        },
    )
)
class PaymentVerifyAPIView(APIView):
    """
    This view handles the user's return from the Zibal payment gateway.
    It receives the trackId and success status from Zibal via query parameters.
    It then immediately calls the verification service to confirm the payment
    with Zibal's server, ensuring a secure verification process.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        track_id = request.query_params.get('trackId')
        success = request.query_params.get('success')

        if not track_id:
            logger.error("Zibal callback received without trackId.")
            return ApiResponse.error(
                message="Required parameter 'trackId' is missing.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if success != '1':
            logger.warning(f"Zibal callback for trackId {track_id} indicates a failed or canceled payment.")
            # Optionally, update the order status to FAILED here if needed.
            return ApiResponse.error(
                message="Payment was not successful or was canceled by the user.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            message = services.verify_payment(track_id)
            # In a real frontend application, you would redirect the user to a success page.
            # For an API, returning a success message is appropriate.
            return ApiResponse.success(
                message=message,
                status_code=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            logger.error(f"Verification failed: No order found for trackId {track_id}.")
            return ApiResponse.error(
                message="Order not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, ZibalGatewayError) as e:
            logger.error(f"Payment verification error for trackId {track_id}: {e}")
            # In a real frontend application, you would redirect the user to a failure page.
            return ApiResponse.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

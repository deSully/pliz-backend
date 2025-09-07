from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from actor.models import Wallet, Merchant
from transaction.errors import PaymentProcessingError
from transaction.serializers import MerchantPaymentSerializer
from transaction.merchants.service import MerchantPaymentService

from drf_yasg.utils import swagger_auto_schema


class MerchantPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=MerchantPaymentSerializer)
    def post(self, request, *args, **kwargs):
        sender = request.user
        serializer = MerchantPaymentSerializer(data=request.data)

        if serializer.is_valid():
            merchant_code = serializer.validated_data["merchant_code"]
            amount = serializer.validated_data["amount"]
            details = serializer.validated_data["details"]

            try:
                sender_wallet = Wallet.objects.get(user__username=sender)
                merchant = Merchant.objects.get(merchant_code=merchant_code)

                response = MerchantPaymentService.process_payment(
                    merchant, sender_wallet, amount, details
                )

                return Response(response, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response(
                    {"detail": str(e), "code": "VALUE_ERROR"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Merchant.DoesNotExist:
                return Response(
                    {
                        "detail": "Le marchand spécifié n'existe pas.",
                        "code": "MERCHANT_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Wallet.DoesNotExist:
                return Response(
                    {
                        "detail": "Le portefeuille de l'envoyeur n'existe pas.",
                        "code": "WALLET_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except PaymentProcessingError as e:
                return Response(
                    {"detail": str(e), "code": "PAYMENT_PROCESSING_ERROR"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except Exception as e:
                return Response(
                    {
                        "detail": "Une erreur inattendue est survenue.",
                        "code": "INTERNAL_SERVER_ERROR",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Renvoie les erreurs du serializer avec détail et code
        field, messages = next(iter(serializer.errors.items()))
        return Response(
            {"detail": messages[0], "code": field.upper() + "_ERROR"},
            status=status.HTTP_400_BAD_REQUEST,
        )

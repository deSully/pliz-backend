from decimal import Decimal

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from transaction.models import TransactionType
from transaction.services.fee import FeeService

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

logger = logging.getLogger(__name__)


class CalculateFeesView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Calculer les frais d'une transaction avant envoi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["amount", "transaction_type"],
            properties={
                "amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Montant de la transaction"),
                "transaction_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["TRANSFER", "TOPUP", "PAYMENT"],
                    description="Type de transaction",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Frais calculés",
                examples={
                    "application/json": {
                        "amount": "10000.00",
                        "fee_amount": "200.00",
                        "total_amount": "10200.00",
                        "transaction_type": "TRANSFER",
                    }
                },
            ),
            400: openapi.Response(description="Données invalides"),
        },
    )
    def post(self, request, *args, **kwargs):
        amount = request.data.get("amount")
        transaction_type = request.data.get("transaction_type")

        if not amount or not transaction_type:
            return Response(
                {"detail": "Les champs 'amount' et 'transaction_type' sont requis.", "code": "MISSING_FIELDS"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(amount))
        except Exception:
            return Response(
                {"detail": "Le montant est invalide.", "code": "INVALID_AMOUNT"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"detail": "Le montant doit être positif.", "code": "INVALID_AMOUNT"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = [t.value for t in TransactionType]
        if transaction_type not in valid_types:
            return Response(
                {
                    "detail": f"Type de transaction invalide. Valeurs acceptées : {', '.join(valid_types)}",
                    "code": "INVALID_TRANSACTION_TYPE",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifier si l'utilisateur est abonné (exonération de frais)
        user = request.user
        if hasattr(user, "is_subscribed") and user.is_subscribed:
            fee_amount = Decimal("0.00")
        else:
            fee = FeeService.get_applicable_fee(transaction_type, amount)
            fee_amount = FeeService.calculate_fee_amount(fee, amount)

        total_amount = amount + fee_amount

        return Response(
            {
                "amount": str(amount),
                "fee_amount": str(fee_amount),
                "total_amount": str(total_amount),
                "transaction_type": transaction_type,
            },
            status=status.HTTP_200_OK,
        )

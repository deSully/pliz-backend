from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transaction.serializers import TopUpSerializer
from drf_yasg.utils import swagger_auto_schema


class TopUpView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=TopUpSerializer)
    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        data["sender"] = user.id

        serializer = TopUpSerializer(data=data, context={"request": request})

        if serializer.is_valid():
            transaction = serializer.save()
            return Response(
                {
                    "detail": "Topup en cours",
                    "code": "TOPUP_PENDING",
                    "transaction_id": transaction.order_id,
                    "payment_url": transaction.additional_data.get("urlTransaction")
                    if transaction.additional_data
                    else None,
                },
                status=status.HTTP_201_CREATED,
            )

        # On renvoie la première erreur du serializer avec detail et code
        field, messages = next(iter(serializer.errors.items()))
        return Response(
            {"detail": messages[0], "code": field.upper() + "_ERROR"},
            status=status.HTTP_400_BAD_REQUEST,
        )

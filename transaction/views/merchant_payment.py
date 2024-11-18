from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from actor.models import Wallet, Merchant
from transaction.errors import PaymentProcessingError
from transaction.serializers import MerchantPaymentSerializer

from transaction.merchants.service import MerchantPaymentService
class MerchantPaymentView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        sender = request.user

        # Serializer pour valider les données de la requête
        serializer = MerchantPaymentSerializer(data=request.data)

        if serializer.is_valid():
            merchant_code = serializer.validated_data['merchant_code']
            amount = serializer.validated_data['amount']
            details = serializer.validated_data['details']

            try:
                # Appeler le service pour traiter le paiement
                sender_wallet = Wallet.objects.get(user=sender)
                merchant = Merchant.objects.get(merchant_code=merchant_code)

                response = MerchantPaymentService.process_payment(merchant, sender_wallet,  amount, details)

                return Response(response, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Merchant.DoesNotExist:
                return Response({"detail": "Le marchand spécifié n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
            except Wallet.DoesNotExist:
                return Response({"detail": "Le portefeuille de l'envoyeur n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
            except PaymentProcessingError as e:
                # Gérer les erreurs lors du traitement du paiement
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                # Gérer toute autre exception inattendue
                return Response({"detail": "Une erreur inattendue est survenue.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

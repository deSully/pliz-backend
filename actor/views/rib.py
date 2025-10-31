from rest_framework import generics, permissions
from actor.models import RIB
from actor.serializers import RIBSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RIBListCreateView(generics.ListCreateAPIView):
    """
    GET: Lister tous les RIBs de l'utilisateur
    POST: Ajouter un nouveau RIB
    """
    serializer_class = RIBSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Lister tous les RIBs de l'utilisateur ou ajouter un nouveau RIB",
        responses={
            200: openapi.Response(
                description="Liste des RIBs",
                examples={
                    "application/json": [
                        {
                            "id": "uuid-123",
                            "bank_name": "Ecobank",
                            "account_number": "SN12345678901234567890",
                            "account_holder": "Mamadou Diallo"
                        }
                    ]
                }
            ),
            201: openapi.Response(
                description="RIB créé avec succès",
                examples={
                    "application/json": {
                        "id": "uuid-456",
                        "bank_name": "CBAO",
                        "account_number": "SN98765432109876543210",
                        "account_holder": "Mamadou Diallo"
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return RIB.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RIBDeleteView(generics.DestroyAPIView):
    """
    DELETE: Supprimer un RIB
    """
    serializer_class = RIBSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Supprimer un RIB de l'utilisateur",
        responses={
            204: "RIB supprimé avec succès",
            404: "RIB non trouvé"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return RIB.objects.filter(user=self.request.user)

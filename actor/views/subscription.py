from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

class ToggleSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_subscribed = not user.is_subscribed
        user.save()
        return Response({
            "message": "Abonnement mis à jour avec succès.",
            "is_subscribed": user.is_subscribed
        }, status=status.HTTP_200_OK)

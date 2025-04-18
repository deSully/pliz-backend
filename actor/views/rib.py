from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from actor.models import RIB
from actor.serializers import RIBSerializer

class RIBListCreateView(generics.ListCreateAPIView):
    serializer_class = RIBSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RIB.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RIBDeleteView(generics.DestroyAPIView):
    serializer_class = RIBSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RIB.objects.filter(user=self.request.user)

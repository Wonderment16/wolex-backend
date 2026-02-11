from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Alert
from .serializers import AlertSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets


class AlertViewSet(ReadOnlyModelViewSet):
    """Read-only viewset for user alerts."""
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user).order_by('-created_at')

    # 🔔 Custom action to mark as read
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response({'status': 'alert marked as read'}, status=status.HTTP_200_OK)    
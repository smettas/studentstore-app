from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification, PushDevice
from .serializers import NotificationSerializer, PushDeviceSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20


class NotificationListView(ListAPIView):
    pagination_class = NotificationPagination
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at", "-pk")


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"marked_read": updated})


class DeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PushDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["expo_push_token"]
        # Reassigning a token invalidates its association with an earlier account.
        with transaction.atomic():
            device, created = PushDevice.objects.update_or_create(
                expo_push_token=token,
                defaults={"user": request.user, "is_active": True},
            )
        return Response({"id": device.pk, "registered": True}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DeviceUnregisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PushDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        count = PushDevice.objects.filter(
            user=request.user,
            expo_push_token=serializer.validated_data["expo_push_token"],
            is_active=True,
        ).update(is_active=False)
        return Response({"unregistered": bool(count)})

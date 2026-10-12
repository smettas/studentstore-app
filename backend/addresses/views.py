from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Address
from .serializers import AddressSerializer


class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by("-is_default", "-created_at")

    def perform_create(self, serializer):
        with transaction.atomic():
            # Lock the user row to serialize concurrent default-address changes.
            type(self.request.user).objects.select_for_update().get(pk=self.request.user.pk)
            default = serializer.validated_data.get("is_default", False)
            if default or not Address.objects.filter(user=self.request.user).exists():
                Address.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
                default = True
            serializer.save(user=self.request.user, is_default=default)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        with transaction.atomic():
            type(self.request.user).objects.select_for_update().get(pk=self.request.user.pk)
            if serializer.validated_data.get("is_default") is True:
                Address.objects.filter(user=self.request.user, is_default=True).exclude(pk=serializer.instance.pk).update(is_default=False)
            serializer.save()


class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            type(request.user).objects.select_for_update().get(pk=request.user.pk)
            address = get_object_or_404(Address, pk=pk, user=request.user)
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.is_default = True
            address.save(update_fields=["is_default"])
        return Response(AddressSerializer(address).data)

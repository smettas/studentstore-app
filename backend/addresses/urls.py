from django.urls import path
from .views import AddressListCreateView, AddressDetailView, SetDefaultAddressView

urlpatterns = [
    path("", AddressListCreateView.as_view(), name="address-list"),
    path("<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
    path("<int:pk>/default/", SetDefaultAddressView.as_view(), name="address-default"),
]

from django.urls import path
from .views import CartView, CartItemListView, CartItemDetailView

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("items/", CartItemListView.as_view(), name="cart-item-add"),
    path("items/<int:item_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
]

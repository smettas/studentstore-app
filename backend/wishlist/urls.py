from django.urls import path
from .views import WishlistView, WishlistItemDetailView

urlpatterns = [
    path("", WishlistView.as_view(), name="wishlist"),
    path("items/<int:item_id>/", WishlistItemDetailView.as_view(), name="wishlist-item-detail"),
]

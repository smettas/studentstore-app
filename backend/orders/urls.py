from django.urls import path
from .views import OrderCancelView, OrderDetailView, OrderListCreateView

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="order-list-create"),
    path("<int:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:order_id>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
]

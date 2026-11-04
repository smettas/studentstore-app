from django.urls import path
from .views import DeliveryCheckView
urlpatterns=[path("check/",DeliveryCheckView.as_view(),name="delivery-check")]

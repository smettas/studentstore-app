from django.urls import path
from .views import ActiveBannerListView

urlpatterns = [
    path("", ActiveBannerListView.as_view(), name="banner-list"),
]

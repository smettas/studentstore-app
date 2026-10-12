from django.urls import path
from .views import dashboard, products, categories, stock, orders, coupons, banners, reports

app_name = "staff_portal"
urlpatterns = [
    path("", dashboard.index, name="dashboard"),
    path("products/", products.index, name="products"),
    path("categories/", categories.index, name="categories"),
    path("stock/", stock.index, name="stock"),
    path("orders/", orders.index, name="orders"),
    path("coupons/", coupons.index, name="coupons"),
    path("banners/", banners.index, name="banners"),
    path("reports/", reports.index, name="reports"),
]

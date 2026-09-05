from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="store_home"),
    path("products/", views.all_products, name="all_products"),  
    path(
        "product/<slug:slug>/",
        views.product_detail,
        name="product_detail"
    ),
    path(
        "cart/",
        views.cart,
        name="cart"
    ),
    path(
        "cart/add/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),
    path(
        "cart/update/<int:product_id>/",
        views.update_cart,
        name="update_cart"
    ),
    path(
        "cart/remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),
]
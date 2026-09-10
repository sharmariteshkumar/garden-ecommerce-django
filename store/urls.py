from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Primary home URL (dono names support honge)
    path("", views.home, name="store_home"),
    path("home/", RedirectView.as_view(pattern_name="store_home", permanent=False), name="home"),
    
    # Store pages
    path("products/", views.all_products, name="all_products"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    
    # Cart actions
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:product_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/",views.checkout,name="checkout"),
    path("payment-success/",views.payment_success,name="payment_success"),
    path("order-success/<int:order_id>/",views.order_success,name="order_success"),
    path("payment-failed/",views.payment_failed,name="payment_failed"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("profile/", views.profile, name="profile"),
    path("orders/<int:order_id>/cancel/",views.cancel_order,name="cancel_order"),
]
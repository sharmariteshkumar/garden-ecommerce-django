from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Category,
    Product,
    Order,
    OrderItem,
)

# =========================================================
# CATEGORY
# =========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    search_fields = (
        "name",
    )


# =========================================================
# PRODUCT
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock",
        "is_available",
        "created_at",
    )

    list_filter = (
        "category",
        "is_available",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }


# =========================================================
# ORDER ITEM INLINE
# =========================================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product_name",
        "price",
        "quantity",
        "total",
    )


# =========================================================
# ORDER
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order_number",
        "customer_name",
        "customer_email",
        "customer_phone",
        "total_amount",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    # Directly edit status & payment_status from admin list view
    list_editable = (
        "payment_status",
        "status",
    )

    list_filter = (
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    search_fields = (
        "order_number",
        "customer_name",
        "customer_email",
        "customer_phone",
        "razorpay_order_id",
        "razorpay_payment_id",
    )

    readonly_fields = (
        "order_number",
        "razorpay_order_id",
        "razorpay_payment_id",
        "created_at",
        "updated_at",
    )

    inlines = [
        OrderItemInline
    ]

    def save_model(self, request, obj, form, change):
        old_status = None

        if change:
            try:
                old_order = Order.objects.get(pk=obj.pk)
                old_status = old_order.status
            except Order.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        # Email only when STATUS is actually changed from admin panel
        if (
            change
            and old_status
            and old_status != obj.status
            and obj.customer_email
        ):
            status_label = obj.get_status_display()

            subject = (
                f"ShopEasy Garden - Order "
                f"{obj.order_number} Status Updated"
            )

            message = f"""Hello {obj.customer_name},

Your order #{obj.order_number} status has been updated.

Order Number: {obj.order_number}
New Status: {status_label}
Payment Status: {obj.get_payment_status_display()}
Total Amount: ₹{obj.total_amount}

Thank you for shopping with ShopEasy Garden.

Regards,
ShopEasy Garden
"""

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=(
                        settings.DEFAULT_FROM_EMAIL
                        or settings.EMAIL_HOST_USER
                    ),
                    recipient_list=[obj.customer_email],
                    fail_silently=False,
                )

                print(
                    f"STATUS EMAIL SENT TO: "
                    f"{obj.customer_email} | "
                    f"{obj.order_number} | "
                    f"{status_label}"
                )

            except Exception as e:
                print(
                    f"STATUS EMAIL FAILED: "
                    f"{obj.customer_email} | "
                    f"{obj.order_number} | "
                    f"{repr(e)}"
                )
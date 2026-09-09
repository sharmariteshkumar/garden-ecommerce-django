from django.contrib import admin
from .email_service import send_brevo_email

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
                html_message = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
                    <h2 style="color: #2e7d32;">
                        ShopEasy Garden
                    </h2>

                    <p>Hello {obj.customer_name},</p>

                    <p>
                        Your order
                        <strong>#{obj.order_number}</strong>
                        status has been updated.
                    </p>

                    <div style="
                        background: #f5f5f5;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 20px 0;
                    ">
                        <p>
                            <strong>Order Number:</strong>
                            {obj.order_number}
                        </p>

                        <p>
                            <strong>New Status:</strong>
                            {status_label}
                        </p>

                        <p>
                            <strong>Payment Status:</strong>
                            {obj.get_payment_status_display()}
                        </p>

                        <p>
                            <strong>Total Amount:</strong>
                            ₹{obj.total_amount}
                        </p>
                    </div>

                    <p>
                        Thank you for shopping with ShopEasy Garden.
                    </p>

                    <p>
                        Regards,<br>
                        <strong>ShopEasy Garden</strong>
                    </p>
                </div>
                """

                email_sent = send_brevo_email(
                    to_email=obj.customer_email,
                    subject=subject,
                    html_content=html_message,
                    to_name=obj.customer_name,
                )

                if email_sent:
                    print(
                        f"STATUS EMAIL SENT TO: "
                        f"{obj.customer_email} | "
                        f"{obj.order_number} | "
                        f"{status_label}"
                    )
                else:
                    print(
                        f"STATUS EMAIL FAILED: "
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
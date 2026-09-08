import os

from django.contrib import admin
from django.contrib import messages
from django.core.mail import send_mail, get_connection

from .models import (
    Category,
    Product,
    Order,
    OrderItem,
)


# =========================================================
# CATEGORY ADMIN
# =========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
    )

    search_fields = (
        "name",
        "slug",
    )


# =========================================================
# PRODUCT ADMIN
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
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
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": (
            "name",
        )
    }


# =========================================================
# ORDER ITEM INLINE
# =========================================================

class OrderItemInline(
    admin.TabularInline
):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product_name",
        "price",
        "quantity",
        "total",
    )


# =========================================================
# DELIVERY EMAIL
# =========================================================

def send_delivery_email_from_admin(
    order
):

    from_email = (
        os.environ.get(
            "DEFAULT_FROM_EMAIL"
        )
        or os.environ.get(
            "EMAIL_HOST_USER"
        )
    )

    if not from_email:

        print(
            "DELIVERY EMAIL SKIPPED: "
            "DEFAULT_FROM_EMAIL / "
            "EMAIL_HOST_USER missing."
        )

        return False

    if not order.customer_email:

        print(
            "DELIVERY EMAIL SKIPPED: "
            "customer email missing."
        )

        return False

    # -----------------------------------------------------
    # SHORT SMTP TIMEOUT
    # -----------------------------------------------------

    try:

        connection = get_connection(
            fail_silently=True,
            timeout=5,
        )

    except Exception as e:

        print(
            "DELIVERY EMAIL CONNECTION ERROR:",
            e
        )

        return False

    # -----------------------------------------------------
    # ITEMS
    # -----------------------------------------------------

    items = []

    for item in order.items.all():

        items.append(
            f"{item.product_name} "
            f"x {item.quantity} "
            f"= ₹{item.total}"
        )

    items_text = "\n".join(
        items
    )

    # -----------------------------------------------------
    # EMAIL
    # -----------------------------------------------------

    subject = (
        f"Order Delivered - "
        f"{order.order_number} - "
        f"ShopEasy Garden"
    )

    message = (
        f"Hello {order.customer_name},\n\n"

        f"Your order has been successfully "
        f"marked as DELIVERED.\n\n"

        f"Order Number: "
        f"{order.order_number}\n"

        f"Order Status: "
        f"Delivered\n"

        f"Payment Status: "
        f"{order.get_payment_status_display()}\n"

        f"Total Amount: "
        f"₹{order.total_amount}\n\n"

        f"Items:\n"
        f"{items_text}\n\n"

        f"Delivery Address:\n"
        f"{order.address}\n"
        f"{order.city}, "
        f"{order.state} - "
        f"{order.pincode}\n\n"

        f"Thank you for shopping with "
        f"ShopEasy Garden.\n\n"

        f"Regards,\n"
        f"ShopEasy Garden"
    )

    try:

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[
                order.customer_email
            ],
            fail_silently=True,
            connection=connection,
        )

        print(
            f"DELIVERY EMAIL SENT: "
            f"{order.order_number}"
        )

        return True

    except Exception as e:

        print(
            "DELIVERY EMAIL ERROR:",
            e
        )

        return False


# =========================================================
# ORDER ADMIN
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
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

    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "order_number",
        "customer_name",
        "customer_email",
        "customer_phone",
        "razorpay_order_id",
        "razorpay_payment_id",
        "payment_id",
    )

    readonly_fields = (
        "order_number",
        "razorpay_order_id",
        "razorpay_payment_id",
        "payment_id",
        "created_at",
        "updated_at",
    )

    inlines = [
        OrderItemInline
    ]

    # -----------------------------------------------------
    # SAVE ORDER
    # -----------------------------------------------------

    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        old_status = None

        # -------------------------------------------------
        # GET OLD STATUS
        # -------------------------------------------------

        if change and obj.pk:

            old_status = (
                Order.objects
                .filter(
                    pk=obj.pk
                )
                .values_list(
                    "status",
                    flat=True
                )
                .first()
            )

        # -------------------------------------------------
        # CHECK WHETHER ORDER IS
        # BECOMING DELIVERED
        # -------------------------------------------------

        becoming_delivered = (
            obj.status == "delivered"
            and old_status != "delivered"
        )

        # -------------------------------------------------
        # SAVE ORDER FIRST
        # -------------------------------------------------

        super().save_model(
            request,
            obj,
            form,
            change
        )

        # -------------------------------------------------
        # SEND DELIVERY EMAIL
        # -------------------------------------------------

        if becoming_delivered:

            email_sent = (
                send_delivery_email_from_admin(
                    obj
                )
            )

            if email_sent:

                self.message_user(
                    request,
                    (
                        f"Order {obj.order_number} "
                        f"marked Delivered. "
                        f"Customer delivery email sent."
                    ),
                    messages.SUCCESS,
                )

            else:

                self.message_user(
                    request,
                    (
                        f"Order {obj.order_number} "
                        f"marked Delivered, but "
                        f"delivery email could not be sent."
                    ),
                    messages.WARNING,
                )
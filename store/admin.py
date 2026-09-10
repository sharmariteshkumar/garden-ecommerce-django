from django.contrib import admin
from django.contrib.admin.helpers import ActionForm
from django import forms
from .email_service import send_customer_email

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

class StockRestoreForm(ActionForm):

    restore_quantity = forms.IntegerField(
        min_value=1,
        label="Quantity to restore",
        help_text="This quantity will be added to the current stock."
    )
    
# =========================================================
# PRODUCT
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    
    action_form = StockRestoreForm

    actions = [
        "restore_stock",
    ]

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

    def restore_stock(self, request, queryset):

        quantity = request.POST.get("restore_quantity")

        if not quantity:

            self.message_user(
                request,
                "Please enter a quantity to restore.",
                level="error"
            )

            return

        try:
            quantity = int(quantity)

        except (TypeError, ValueError):

            self.message_user(
                request,
                "Please enter a valid quantity.",
                level="error"
            )

            return

        if quantity < 1:

            self.message_user(
                request,
                "Quantity must be at least 1.",
                level="error"
            )

            return

        updated = 0

        for product in queryset:

            product.stock += quantity

            product.save(
                update_fields=[
                    "stock",
                    "updated_at",
                ]
            )

            updated += 1

        self.message_user(
            request,
            f"Stock restored by {quantity} for {updated} product(s)."
        )

    restore_stock.short_description = "Restore stock"

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

        # Save order first
        super().save_model(request, obj, form, change)

        # =====================================================
        # SEND EMAIL ONLY WHEN ORDER STATUS CHANGES
        # =====================================================

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

                email_sent = send_customer_email(
                    to_email=obj.customer_email,
                    subject=subject,
                    message=message,
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
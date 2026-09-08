from django.db import models
import uuid
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("online", "Online Payment"),
    ]

    order_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    shipping_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="online"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = "GRD-" + uuid.uuid4().hex[:10].upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_name = models.CharField(max_length=200)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField()

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
@receiver(pre_save, sender=Order)
def notify_delivery_status(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_order = Order.objects.get(pk=instance.pk)
        # Old status delivered nahi tha par ab Admin ne Delivered set kiya hai
        if old_order.status != 'delivered' and instance.status == 'delivered':
            if instance.customer_email:
                subject = f"Order Delivered - #{instance.order_number}"
                message = (
                    f"Hello {instance.customer_name},\n\n"
                    f"Great news! Your order #{instance.order_number} has been successfully delivered.\n\n"
                    f"Thank you for shopping with ShopEasy Garden!"
                )
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL or os.environ.get("EMAIL_HOST_USER"),
                    recipient_list=[instance.customer_email],
                    fail_silently=True,
                )
                print(f"DELIVERY EMAIL SENT TO: {instance.customer_email}")
    except Order.DoesNotExist:
        pass
import os
from decimal import Decimal

import razorpay

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Product, Category, Order, OrderItem


# =========================================================
# RAZORPAY CLIENT
# =========================================================

def get_razorpay_client():
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are missing."
        )

    return razorpay.Client(
        auth=(key_id, key_secret)
    )


# =========================================================
# CART HELPER
# =========================================================

def get_cart_items(request):

    cart_data = request.session.get("cart", {})

    if not cart_data:
        return [], Decimal("0.00")

    product_ids = cart_data.keys()

    products = Product.objects.filter(
        id__in=product_ids,
        is_available=True
    )

    cart_items = []
    total = Decimal("0.00")

    cleaned_cart = {}

    for product in products:

        try:
            quantity = int(cart_data.get(str(product.id), 0))
        except (TypeError, ValueError):
            quantity = 0

        if quantity <= 0:
            continue

        # Never allow cart quantity above stock
        quantity = min(quantity, product.stock)

        if quantity <= 0:
            continue

        item_total = product.price * quantity
        total += item_total

        cleaned_cart[str(product.id)] = quantity

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "total": item_total,
        })

    if cleaned_cart != cart_data:
        request.session["cart"] = cleaned_cart
        request.session.modified = True

    return cart_items, total


# =========================================================
# HOME
# =========================================================

def home(request):

    products = Product.objects.filter(
        is_available=True,
        stock__gt=0
    ).order_by("-created_at")

    categories = Category.objects.all()

    return render(
        request,
        "store/home.html",
        {
            "products": products,
            "categories": categories,
        }
    )


# =========================================================
# PRODUCT DETAIL
# =========================================================

def product_detail(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug,
        is_available=True
    )

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product
        }
    )


# =========================================================
# ADD TO CART
# =========================================================

@require_POST
def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.stock <= 0:
        messages.error(
            request,
            "Sorry, this product is out of stock."
        )
        return redirect("product_detail", slug=product.slug)

    quantity = min(quantity, product.stock)

    cart = request.session.get("cart", {})

    current_quantity = int(
        cart.get(str(product.id), 0)
    )

    new_quantity = min(
        current_quantity + quantity,
        product.stock
    )

    cart[str(product.id)] = new_quantity

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(
        request,
        f"{product.name} added to cart."
    )

    return redirect("cart")


# =========================================================
# CART
# =========================================================

def cart(request):

    cart_items, total = get_cart_items(request)

    return render(
        request,
        "store/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
    )


# =========================================================
# UPDATE CART
# =========================================================

@require_POST
def update_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    try:
        quantity = int(
            request.POST.get("quantity", 1)
        )
    except (TypeError, ValueError):
        quantity = 1

    cart = request.session.get("cart", {})

    if quantity <= 0:
        cart.pop(str(product.id), None)

    else:
        quantity = min(quantity, product.stock)

        if quantity > 0:
            cart[str(product.id)] = quantity
        else:
            cart.pop(str(product.id), None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# REMOVE FROM CART
# =========================================================

@require_POST
def remove_from_cart(request, product_id):

    cart = request.session.get("cart", {})

    cart.pop(str(product_id), None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# ALL PRODUCTS
# =========================================================

def all_products(request):

    products = Product.objects.filter(
        is_available=True
    )

    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get(
        "category",
        ""
    ).strip()

    sort = request.GET.get(
        "sort",
        "newest"
    )

    if query:

        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
        )

    if category_slug:

        products = products.filter(
            category__slug=category_slug
        )

    if sort == "price_low":
        products = products.order_by("price")

    elif sort == "price_high":
        products = products.order_by("-price")

    elif sort == "name":
        products = products.order_by("name")

    else:
        products = products.order_by("-created_at")

    return render(
        request,
        "store/all_products.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "category": category_slug,
            "sort": sort,
        }
    )


# =========================================================
# CHECKOUT
# =========================================================

def checkout(request):

    cart_items, total = get_cart_items(request)

    if not cart_items:
        messages.warning(
            request,
            "Your cart is empty."
        )
        return redirect("cart")

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        state = request.POST.get(
            "state",
            ""
        ).strip()

        pin_code = request.POST.get("pincode", "").strip()

        # -------------------------
        # Required fields
        # -------------------------

        if not all([
            full_name,
            email,
            phone,
            address,
            city,
            state,
            pin_code,
        ]):

            messages.error(
                request,
                "Please fill all required fields."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # -------------------------
        # Email validation
        # -------------------------

        try:
            validate_email(email)
        except ValidationError:

            messages.error(
                request,
                "Please enter a valid email address."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # -------------------------
        # Razorpay
        # -------------------------

        try:

            client = get_razorpay_client()

            amount_paise = int(
                total * Decimal("100")
            )

            if not request.session.session_key:
                request.session.create()

            receipt = (
                f"grd_{request.session.session_key}"
            )

            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "payment_capture": 1,
            })

        except Exception as e:

            print("RAZORPAY ORDER ERROR:", e)

            messages.error(
                request,
                "Unable to start payment. Please try again."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # -------------------------
        # Create local order
        # -------------------------

        try:

            with transaction.atomic():

                order = Order.objects.create(
                    customer_name=full_name,
                    customer_email=email,
                    customer_phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    pincode=pin_code,
                    subtotal=total,
                    shipping_charge=Decimal("0.00"),
                    total_amount=total,
                    payment_method="online",
                    payment_status="pending",
                    status="pending",
                    razorpay_order_id=razorpay_order["id"],
                )

                for item in cart_items:

                    OrderItem.objects.create(
                        order=order,
                        product=item["product"],
                        product_name=item["product"].name,
                        price=item["product"].price,
                        quantity=item["quantity"],
                        total=item["total"],
                    )

        except Exception as e:

            print("ORDER CREATE ERROR:", e)

            messages.error(
                request,
                "Unable to create order. Please try again."
            )

            return redirect("checkout")

        # -------------------------
        # Payment page
        # -------------------------

        return render(
            request,
            "store/payment.html",
            {
                "order": order,
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key_id": os.environ.get(
                    "RAZORPAY_KEY_ID"
                ),
                "amount": int(total * Decimal("100")),
                "total": total,
            }
        )

    return render(
        request,
        "store/checkout.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
    )


# =========================================================
# SEND ORDER EMAILS
# =========================================================

def send_order_emails(order):
    from_email = (
        os.environ.get("DEFAULT_FROM_EMAIL")
        or os.environ.get("EMAIL_HOST_USER")
    )
    admin_email = os.environ.get("ADMIN_EMAIL")

    if not from_email:
        print("EMAIL NOT SENT: DEFAULT_FROM_EMAIL is missing in environment variables.")
        return

    items_text = "\n".join([f"- {item.product_name} x {item.quantity} = ₹{item.total}" for item in order.items.all()])

    # Customer Email
    customer_subject = f"ShopEasy Garden - Order {order.order_number} Confirmed"
    customer_message = f"""Hello {order.customer_name},

Thank you for your order!

Order Number: {order.order_number}
Payment Status: {order.payment_status.upper()}
Total Amount: ₹{order.total_amount}

Items Ordered:
{items_text}

Delivery Address:
{order.address}, {order.city}, {order.state} - {order.pincode}

We will notify you once your order is delivered!
"""

    try:
        send_mail(
            customer_subject,
            customer_message,
            from_email,
            [order.customer_email],
            fail_silently=False,  # Isse exact error terminal/logs me dikhega agar send na ho
        )
        print(f"CONFIRMATION EMAIL SENT TO: {order.customer_email}")
    except Exception as e:
        print("CUSTOMER EMAIL FAILED:", repr(e))

    # Admin Email (Optional)
    if admin_email:
        try:
            send_mail(
                f"New Order #{order.order_number} Received",
                f"New order placed by {order.customer_name} ({order.customer_email}) for amount ₹{order.total_amount}.",
                from_email,
                [admin_email],
                fail_silently=True,
            )
        except Exception as e:
            print("ADMIN EMAIL FAILED:", repr(e))

    # -------------------------
    # Admin email
    # -------------------------

    if admin_email:

        admin_subject = (
            f"New ShopEasy Garden Order - "
            f"{order.order_number}"
        )

        admin_message = f"""
New order received.

Order Number: {order.order_number}

Customer:
{order.customer_name}

Email:
{order.customer_email}

Phone:
{order.customer_phone}

Amount:
₹{order.total_amount}

Payment ID:
{order.razorpay_payment_id}

Items:
{items_text}

Address:
{order.address}
{order.city}, {order.state} - {order.pincode}
"""

        try:

            send_mail(
                admin_subject,
                admin_message,
                from_email,
                [admin_email],
                fail_silently=True,
            )

        except Exception as e:

            print(
                "ADMIN EMAIL ERROR:",
                e
            )


# =========================================================
# PAYMENT SUCCESS
# =========================================================

@csrf_exempt
@require_POST
def payment_success(request):

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    if not all([
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ]):

        return redirect("payment_failed")

    try:

        client = get_razorpay_client()

        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })

    except Exception as e:

        print("========== RAZORPAY SIGNATURE ERROR ==========")
        print("ERROR:", repr(e))
        print("ORDER ID:", razorpay_order_id)
        print("PAYMENT ID:", razorpay_payment_id)
        print("SIGNATURE:", razorpay_signature)
        print("===============================================")

        return redirect("payment_failed")

    try:

        with transaction.atomic():

            order = Order.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id
            )

            # Prevent duplicate stock deduction
            if order.payment_status != "paid":

                for item in order.items.select_related(
                    "product"
                ):

                    product = item.product

                    if not product:
                        continue

                    if product.stock < item.quantity:

                        raise ValueError(
                            f"Insufficient stock for "
                            f"{product.name}"
                        )

                # Deduct stock ONLY after successful payment
                for item in order.items.select_related(
                    "product"
                ):

                    if item.product:

                        item.product.stock -= item.quantity

                        item.product.save(
                            update_fields=[
                                "stock",
                                "updated_at",
                            ]
                        )

                order.razorpay_payment_id = (
                    razorpay_payment_id
                )

                order.payment_status = "paid"
                order.payment_method = "online"
                order.status = "confirmed"

                order.save()
                

            else:

                # Already processed payment
                pass

    except Exception as e:

        print(
            "PAYMENT PROCESSING ERROR:",
            e
        )

        return redirect("payment_failed")

    # -------------------------
    # Email after successful payment
    # -------------------------

    try:
        send_order_emails(order)
    except Exception as e:
        print(
            "EMAIL PROCESS ERROR:",
            e
        )

    # -------------------------
    # Clear cart ONLY after payment
    # -------------------------

    request.session["cart"] = {}
    request.session.modified = True

    return redirect(
        "order_success",
        order_id=order.id
    )


# =========================================================
# ORDER SUCCESS
# =========================================================

def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    return render(
        request,
        "store/order_success.html",
        {
            "order": order
        }
    )


# =========================================================
# PAYMENT FAILED
# =========================================================

def payment_failed(request):

    reason = request.GET.get(
        "reason",
        "Payment could not be completed."
    )

    return render(
        request,
        "store/payment_failed.html",
        {
            "reason": reason
        }
    )
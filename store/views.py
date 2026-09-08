import os
from decimal import Decimal

import razorpay

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Product, Category, Order, OrderItem


# =========================================================
# HOME
# =========================================================

def home(request):

    products = Product.objects.filter(
        is_available=True
    )

    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
        )

    return render(
        request,
        "store/home.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
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
        quantity = int(
            request.POST.get(
                "quantity",
                1
            )
        )
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.stock < 1:
        messages.error(
            request,
            "This product is out of stock."
        )

        return redirect("all_products")

    cart = request.session.get(
        "cart",
        {}
    )

    product_id = str(product.id)

    current_quantity = int(
        cart.get(
            product_id,
            0
        )
    )

    new_quantity = current_quantity + quantity

    if new_quantity > product.stock:
        new_quantity = product.stock

    cart[product_id] = new_quantity

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# CART
# =========================================================

def cart(request):

    cart_data = request.session.get(
        "cart",
        {}
    )

    products = Product.objects.filter(
        id__in=cart_data.keys(),
        is_available=True
    )

    cart_items = []

    total = Decimal("0.00")

    for product in products:

        quantity = int(
            cart_data.get(
                str(product.id),
                0
            )
        )

        if quantity <= 0:
            continue

        if quantity > product.stock:
            quantity = product.stock

            cart_data[
                str(product.id)
            ] = quantity

        if quantity <= 0:
            continue

        item_total = (
            product.price * quantity
        )

        total += item_total

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

    request.session["cart"] = cart_data
    request.session.modified = True

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

    try:
        quantity = int(
            request.POST.get(
                "quantity",
                1
            )
        )
    except (ValueError, TypeError):
        quantity = 1

    cart = request.session.get(
        "cart",
        {}
    )

    product_id = str(product_id)

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if quantity <= 0:

        cart.pop(
            product_id,
            None
        )

    else:

        quantity = min(
            quantity,
            product.stock
        )

        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(
                product_id,
                None
            )

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# REMOVE FROM CART
# =========================================================

@require_POST
def remove_from_cart(request, product_id):

    cart = request.session.get(
        "cart",
        {}
    )

    cart.pop(
        str(product_id),
        None
    )

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

    query = request.GET.get(
        "q",
        ""
    ).strip()

    category_slug = request.GET.get(
        "category",
        ""
    )

    sort = request.GET.get(
        "sort",
        ""
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

    if sort == "price_asc":

        products = products.order_by(
            "price"
        )

    elif sort == "price_desc":

        products = products.order_by(
            "-price"
        )

    elif sort == "newest":

        products = products.order_by(
            "-created_at"
        )

    return render(
        request,
        "store/all_products.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
        }
    )


# =========================================================
# CHECKOUT
# =========================================================

def checkout(request):

    cart_data = request.session.get(
        "cart",
        {}
    )

    if not cart_data:
        return redirect("cart")

    products = Product.objects.filter(
        id__in=cart_data.keys(),
        is_available=True
    )

    cart_items = []

    total = Decimal("0.00")

    for product in products:

        quantity = int(
            cart_data.get(
                str(product.id),
                0
            )
        )

        if quantity <= 0:
            continue

        if quantity > product.stock:
            quantity = product.stock

        if quantity <= 0:
            continue

        item_total = (
            product.price * quantity
        )

        total += item_total

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

    if not cart_items:
        return redirect("cart")

    # -----------------------------------------------------
    # POST = CREATE RAZORPAY ORDER
    # -----------------------------------------------------

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

        pin_code = request.POST.get(
            "pin_code",
            ""
        ).strip()

        # Required fields
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

        # Email validation
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

        key_id = os.environ.get(
            "RAZORPAY_KEY_ID"
        )

        key_secret = os.environ.get(
            "RAZORPAY_KEY_SECRET"
        )

        if not key_id or not key_secret:

            messages.error(
                request,
                "Razorpay configuration is missing."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # Razorpay client
        client = razorpay.Client(
            auth=(
                key_id,
                key_secret
            )
        )

        # Razorpay amount in paise
        razorpay_order = client.order.create({
            "amount": int(
                total * 100
            ),
            "currency": "INR",
            "receipt": (
                f"receipt_"
                f"{request.session.session_key}"
            ),
        })

        # -------------------------------------------------
        # CREATE LOCAL ORDER
        # -------------------------------------------------

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

            razorpay_order_id=(
                razorpay_order["id"]
            ),
        )

        # -------------------------------------------------
        # CREATE ORDER ITEMS
        # -------------------------------------------------

        for item in cart_items:

            OrderItem.objects.create(

                order=order,

                product=item["product"],

                product_name=(
                    item["product"].name
                ),

                price=(
                    item["product"].price
                ),

                quantity=item["quantity"],

                total=item["item_total"],
            )

        return render(
            request,
            "store/payment.html",
            {
                "order": order,

                "razorpay_order_id": (
                    razorpay_order["id"]
                ),

                "razorpay_key_id": key_id,

                "amount": int(
                    total * 100
                ),

                "total": total,
            }
        )

    # -----------------------------------------------------
    # GET CHECKOUT
    # -----------------------------------------------------

    return render(
        request,
        "store/checkout.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
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

        return redirect(
            "payment_failed"
        )

    try:

        key_id = os.environ.get(
            "RAZORPAY_KEY_ID"
        )

        key_secret = os.environ.get(
            "RAZORPAY_KEY_SECRET"
        )

        client = razorpay.Client(
            auth=(
                key_id,
                key_secret
            )
        )

        # -------------------------------------------------
        # VERIFY PAYMENT
        # -------------------------------------------------

        client.utility.verify_payment_signature({
            "razorpay_order_id": (
                razorpay_order_id
            ),

            "razorpay_payment_id": (
                razorpay_payment_id
            ),

            "razorpay_signature": (
                razorpay_signature
            ),
        })

        order = get_object_or_404(
            Order,
            razorpay_order_id=(
                razorpay_order_id
            )
        )

        # Prevent duplicate payment processing
        if order.payment_status == "paid":

            return redirect(
                "order_success",
                order_id=order.id
            )

        # -------------------------------------------------
        # UPDATE ORDER + STOCK
        # -------------------------------------------------

        with transaction.atomic():

            for item in order.items.select_related(
                "product"
            ):

                product = item.product

                if not product:
                    continue

                if product.stock < item.quantity:

                    raise ValueError(
                        f"Not enough stock for "
                        f"{product.name}"
                    )

            for item in order.items.select_related(
                "product"
            ):

                product = item.product

                if not product:
                    continue

                product.stock -= item.quantity

                if product.stock <= 0:

                    product.stock = 0
                    product.is_available = False

                product.save(
                    update_fields=[
                        "stock",
                        "is_available",
                        "updated_at",
                    ]
                )

            order.status = "confirmed"

            order.payment_status = "paid"

            order.payment_method = "online"

            order.razorpay_payment_id = (
                razorpay_payment_id
            )

            order.payment_id = (
                razorpay_payment_id
            )

            order.save(
                update_fields=[
                    "status",
                    "payment_status",
                    "payment_method",
                    "razorpay_payment_id",
                    "payment_id",
                    "updated_at",
                ]
            )

        # -------------------------------------------------
        # CUSTOMER EMAIL
        # -------------------------------------------------

        from_email = os.environ.get(
            "DEFAULT_FROM_EMAIL"
        )

        if from_email:

            send_mail(

                subject=(
                    f"Order #{order.order_number} "
                    f"Confirmed - ShopEasy"
                ),

                message=(
                    f"Hello {order.customer_name},\n\n"

                    f"Your order has been "
                    f"successfully placed.\n\n"

                    f"Order Number: "
                    f"{order.order_number}\n"

                    f"Amount Paid: "
                    f"₹{order.total_amount}\n"

                    f"Payment ID: "
                    f"{order.razorpay_payment_id}\n\n"

                    f"Thank you for shopping "
                    f"with ShopEasy!"
                ),

                from_email=from_email,

                recipient_list=[
                    order.customer_email
                ],

                fail_silently=True,
            )

        # -------------------------------------------------
        # ADMIN EMAIL
        # -------------------------------------------------

        admin_email = os.environ.get(
            "ADMIN_EMAIL"
        )

        if from_email and admin_email:

            send_mail(

                subject=(
                    f"New Order "
                    f"{order.order_number} - ShopEasy"
                ),

                message=(
                    f"New order received.\n\n"

                    f"Order Number: "
                    f"{order.order_number}\n"

                    f"Customer: "
                    f"{order.customer_name}\n"

                    f"Email: "
                    f"{order.customer_email}\n"

                    f"Phone: "
                    f"{order.customer_phone}\n"

                    f"Amount: "
                    f"₹{order.total_amount}\n"

                    f"Payment ID: "
                    f"{order.razorpay_payment_id}\n"
                ),

                from_email=from_email,

                recipient_list=[
                    admin_email
                ],

                fail_silently=True,
            )

        # -------------------------------------------------
        # CLEAR CART ONLY AFTER PAYMENT
        # -------------------------------------------------

        request.session["cart"] = {}

        request.session.modified = True

        return redirect(
            "order_success",
            order_id=order.id
        )

    except Exception as e:

        print(
            "PAYMENT ERROR:",
            e
        )

        return redirect(
            "payment_failed"
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

    return render(
        request,
        "store/payment_failed.html"
    )
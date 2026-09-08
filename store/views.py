import os
from decimal import Decimal

import razorpay

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail, get_connection
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Product, Category, Order, OrderItem


# =========================================================
# RAZORPAY CLIENT
# =========================================================

def get_razorpay_client():

    key_id = os.environ.get(
        "RAZORPAY_KEY_ID"
    )

    key_secret = os.environ.get(
        "RAZORPAY_KEY_SECRET"
    )

    if not key_id or not key_secret:
        raise ValueError(
            "RAZORPAY_KEY_ID or "
            "RAZORPAY_KEY_SECRET is missing."
        )

    return razorpay.Client(
        auth=(
            key_id,
            key_secret
        )
    )


# =========================================================
# EMAIL CONNECTION
# =========================================================

def get_email_connection():

    try:
        return get_connection(
            fail_silently=True,
            timeout=5,
        )
    except Exception as e:
        print(
            "EMAIL CONNECTION ERROR:",
            e
        )
        return None


# =========================================================
# ORDER PLACED EMAILS
# =========================================================

def send_order_emails(order):

    from_email = (
        os.environ.get(
            "DEFAULT_FROM_EMAIL"
        )
        or os.environ.get(
            "EMAIL_HOST_USER"
        )
    )

    admin_email = os.environ.get(
        "ADMIN_EMAIL"
    )

    if not from_email:
        print(
            "ORDER EMAIL SKIPPED: "
            "DEFAULT_FROM_EMAIL / EMAIL_HOST_USER missing."
        )
        return

    connection = get_email_connection()

    if connection is None:
        print(
            "ORDER EMAIL SKIPPED: "
            "Could not create email connection."
        )
        return

    # -----------------------------------------------------
    # ITEMS
    # -----------------------------------------------------

    items_text = []

    for item in order.items.all():

        items_text.append(
            f"{item.product_name} "
            f"x {item.quantity} "
            f"= ₹{item.total}"
        )

    items_text = "\n".join(
        items_text
    )

    # -----------------------------------------------------
    # CUSTOMER EMAIL
    # -----------------------------------------------------

    customer_subject = (
        f"Order Placed - "
        f"{order.order_number} - "
        f"ShopEasy Garden"
    )

    customer_message = (
        f"Hello {order.customer_name},\n\n"

        f"Thank you for shopping with "
        f"ShopEasy Garden.\n\n"

        f"Your order has been successfully "
        f"placed and payment has been received.\n\n"

        f"Order Number: "
        f"{order.order_number}\n"

        f"Order Status: "
        f"{order.get_status_display()}\n"

        f"Payment Status: "
        f"{order.get_payment_status_display()}\n"

        f"Payment ID: "
        f"{order.razorpay_payment_id or order.payment_id or 'N/A'}\n"

        f"Total Amount: "
        f"₹{order.total_amount}\n\n"

        f"Items:\n"
        f"{items_text}\n\n"

        f"Delivery Address:\n"
        f"{order.address}\n"
        f"{order.city}, "
        f"{order.state} - "
        f"{order.pincode}\n\n"

        f"We will update you when your order "
        f"is delivered.\n\n"

        f"Thank you,\n"
        f"ShopEasy Garden"
    )

    try:

        if order.customer_email:

            send_mail(
                subject=customer_subject,
                message=customer_message,
                from_email=from_email,
                recipient_list=[
                    order.customer_email
                ],
                fail_silently=True,
                connection=connection,
            )

    except Exception as e:

        print(
            "CUSTOMER ORDER EMAIL ERROR:",
            e
        )

    # -----------------------------------------------------
    # ADMIN EMAIL
    # -----------------------------------------------------

    if admin_email:

        admin_subject = (
            f"New Order - "
            f"{order.order_number} - "
            f"ShopEasy Garden"
        )

        admin_message = (
            f"New order received.\n\n"

            f"Order Number: "
            f"{order.order_number}\n"

            f"Customer: "
            f"{order.customer_name}\n"

            f"Email: "
            f"{order.customer_email}\n"

            f"Phone: "
            f"{order.customer_phone}\n\n"

            f"Address:\n"
            f"{order.address}\n"
            f"{order.city}, "
            f"{order.state} - "
            f"{order.pincode}\n\n"

            f"Total Amount: "
            f"₹{order.total_amount}\n"

            f"Payment Method: "
            f"{order.get_payment_method_display()}\n"

            f"Payment Status: "
            f"{order.get_payment_status_display()}\n"

            f"Payment ID: "
            f"{order.razorpay_payment_id or order.payment_id or 'N/A'}\n"

            f"Order Status: "
            f"{order.get_status_display()}\n\n"

            f"Items:\n"
            f"{items_text}\n"
        )

        try:

            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email=from_email,
                recipient_list=[
                    admin_email
                ],
                fail_silently=True,
                connection=connection,
            )

        except Exception as e:

            print(
                "ADMIN ORDER EMAIL ERROR:",
                e
            )


# =========================================================
# DELIVERY EMAIL
# =========================================================

def send_delivery_email(order):

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
            "DEFAULT_FROM_EMAIL / EMAIL_HOST_USER missing."
        )
        return False

    if not order.customer_email:
        print(
            "DELIVERY EMAIL SKIPPED: "
            "Customer email missing."
        )
        return False

    connection = get_email_connection()

    if connection is None:
        return False

    items_text = []

    for item in order.items.all():

        items_text.append(
            f"{item.product_name} "
            f"x {item.quantity} "
            f"= ₹{item.total}"
        )

    items_text = "\n".join(
        items_text
    )

    subject = (
        f"Order Delivered - "
        f"{order.order_number} - "
        f"ShopEasy Garden"
    )

    message = (
        f"Hello {order.customer_name},\n\n"

        f"Great news!\n\n"

        f"Your ShopEasy Garden order has "
        f"been marked as DELIVERED.\n\n"

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
# HOME
# =========================================================

def home(request):

    products = Product.objects.filter(
        is_available=True
    )

    categories = Category.objects.all()

    query = request.GET.get(
        "q",
        ""
    ).strip()

    if query:

        products = products.filter(
            Q(name__icontains=query)
            |
            Q(description__icontains=query)
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

    except (
        ValueError,
        TypeError
    ):

        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.stock < 1:

        messages.error(
            request,
            "This product is out of stock."
        )

        return redirect(
            "all_products"
        )

    cart = request.session.get(
        "cart",
        {}
    )

    product_id = str(
        product.id
    )

    current_quantity = int(
        cart.get(
            product_id,
            0
        )
    )

    new_quantity = (
        current_quantity
        + quantity
    )

    if new_quantity > product.stock:

        new_quantity = (
            product.stock
        )

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
            product.price
            * quantity
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
def update_cart(
    request,
    product_id
):

    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1
            )
        )

    except (
        ValueError,
        TypeError
    ):

        quantity = 1

    cart = request.session.get(
        "cart",
        {}
    )

    product_id = str(
        product_id
    )

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
def remove_from_cart(
    request,
    product_id
):

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
            |
            Q(description__icontains=query)
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
            product.price
            * quantity
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

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

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

        # -------------------------------------------------
        # EMAIL VALIDATION
        # -------------------------------------------------

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

        # -------------------------------------------------
        # RAZORPAY CONFIG
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CREATE RAZORPAY ORDER
        # -------------------------------------------------

        try:

            client = get_razorpay_client()

            razorpay_order = (
                client.order.create({
                    "amount": int(
                        total * 100
                    ),
                    "currency": "INR",
                    "receipt": (
                        f"grd_"
                        f"{request.session.session_key}"
                    ),
                    "payment_capture": 1,
                })
            )

        except Exception as e:

            print(
                "RAZORPAY ORDER ERROR:",
                e
            )

            messages.error(
                request,
                "Unable to start payment. "
                "Please try again."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

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

            shipping_charge=Decimal(
                "0.00"
            ),

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

    # -----------------------------------------------------
    # REQUIRED RAZORPAY DATA
    # -----------------------------------------------------

    if not all([
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ]):

        return redirect(
            "payment_failed"
        )

    try:

        # -------------------------------------------------
        # VERIFY PAYMENT
        # -------------------------------------------------

        client = get_razorpay_client()

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

        # -------------------------------------------------
        # GET ORDER
        # -------------------------------------------------

        order = get_object_or_404(
            Order,
            razorpay_order_id=(
                razorpay_order_id
            )
        )

        # -------------------------------------------------
        # ALREADY PAID
        # -------------------------------------------------

        if order.payment_status == "paid":

            request.session["cart"] = {}

            request.session.modified = True

            return redirect(
                "order_success",
                order_id=order.id
            )

        # -------------------------------------------------
        # PAYMENT + STOCK UPDATE
        # -------------------------------------------------

        with transaction.atomic():

            order = (
                Order.objects
                .select_for_update()
                .get(
                    pk=order.pk
                )
            )

            # Another request may have
            # completed the payment.

            if order.payment_status == "paid":

                request.session["cart"] = {}

                request.session.modified = True

                return redirect(
                    "order_success",
                    order_id=order.id
                )

            # -------------------------------------------------
            # CHECK STOCK FIRST
            # -------------------------------------------------

            order_items = list(
                order.items.select_related(
                    "product"
                )
            )

            for item in order_items:

                product = item.product

                if not product:
                    continue

                if product.stock < item.quantity:

                    raise ValueError(
                        f"Not enough stock for "
                        f"{product.name}"
                    )

            # -------------------------------------------------
            # REDUCE STOCK
            # -------------------------------------------------

            for item in order_items:

                product = item.product

                if not product:
                    continue

                product.stock -= (
                    item.quantity
                )

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

            # -------------------------------------------------
            # MARK ORDER CONFIRMED
            # -------------------------------------------------

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

        # -----------------------------------------------------
        # PAYMENT IS NOW SUCCESSFUL
        # -----------------------------------------------------
        #
        # Email failure MUST NOT change
        # successful payment into failed payment.
        # -----------------------------------------------------

        try:

            send_order_emails(
                order
            )

        except Exception as e:

            print(
                "ORDER EMAIL ERROR:",
                e
            )

        # -----------------------------------------------------
        # CLEAR CART
        # -----------------------------------------------------

        request.session["cart"] = {}

        request.session.modified = True

        # -----------------------------------------------------
        # SUCCESS PAGE
        # -----------------------------------------------------

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

def order_success(
    request,
    order_id
):

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
        ""
    )

    return render(
        request,
        "store/payment_failed.html",
        {
            "reason": reason,
        }
    )
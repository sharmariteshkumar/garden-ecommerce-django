import os
import re
from django.core.validators import validate_email
from decimal import Decimal

import razorpay

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .email_service import send_customer_email
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Product, Category, Order, OrderItem

# =========================================================
# INDIA STATE -> CITY VALIDATION
# =========================================================

STATE_CITIES = {
    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool",
        "Tirupati", "Rajahmundry", "Kakinada"
    ],

    "Arunachal Pradesh": [
        "Itanagar", "Naharlagun", "Pasighat", "Tawang"
    ],

    "Assam": [
        "Guwahati", "Dibrugarh", "Silchar", "Jorhat", "Tezpur"
    ],

    "Bihar": [
        "Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga"
    ],

    "Chhattisgarh": [
        "Raipur", "Bhilai", "Bilaspur", "Korba", "Durg"
    ],

    "Goa": [
        "Panaji", "Margao", "Vasco da Gama", "Mapusa"
    ],

    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar",
        "Jamnagar", "Gandhinagar", "Junagadh"
    ],

    "Haryana": [
        "Gurugram", "Faridabad", "Panipat", "Ambala", "Hisar",
        "Rohtak", "Karnal"
    ],

    "Himachal Pradesh": [
        "Shimla", "Dharamshala", "Mandi", "Solan", "Kullu"
    ],

    "Jharkhand": [
        "Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar"
    ],

    "Karnataka": [
        "Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi",
        "Davanagere", "Ballari", "Shivamogga"
    ],

    "Kerala": [
        "Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur",
        "Kollam", "Kannur", "Alappuzha"
    ],

    "Madhya Pradesh": [
        "Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain",
        "Sagar", "Rewa"
    ],

    "Maharashtra": [
        "Mumbai", "Pune", "Nagpur", "Nashik", "Thane",
        "Aurangabad", "Navi Mumbai", "Kolhapur", "Solapur",
        "Amravati", "Satara", "Sangli", "Jalgaon", "Akola"
    ],

    "Manipur": [
        "Imphal", "Thoubal", "Bishnupur"
    ],

    "Meghalaya": [
        "Shillong", "Tura", "Jowai"
    ],

    "Mizoram": [
        "Aizawl", "Lunglei", "Champhai"
    ],

    "Nagaland": [
        "Kohima", "Dimapur", "Mokokchung"
    ],

    "Odisha": [
        "Bhubaneswar", "Cuttack", "Rourkela", "Puri", "Berhampur",
        "Sambalpur"
    ],

    "Punjab": [
        "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda",
        "Mohali", "Pathankot"
    ],

    "Rajasthan": [
        "Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer",
        "Bikaner", "Alwar", "Bharatpur"
    ],

    "Sikkim": [
        "Gangtok", "Namchi", "Gyalshing"
    ],

    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli",
        "Salem", "Tirunelveli", "Vellore", "Erode", "Thoothukudi"
    ],

    "Telangana": [
        "Hyderabad", "Warangal", "Nizamabad", "Karimnagar",
        "Khammam"
    ],

    "Tripura": [
        "Agartala", "Udaipur", "Dharmanagar"
    ],

    "Uttar Pradesh": [
        "Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj",
        "Ghaziabad", "Noida", "Meerut", "Bareilly", "Aligarh",
        "Moradabad", "Gorakhpur"
    ],

    "Uttarakhand": [
        "Dehradun", "Haridwar", "Nainital", "Haldwani",
        "Rishikesh", "Roorkee"
    ],

    "West Bengal": [
        "Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri",
        "Darjeeling"
    ],

    "Delhi": [
        "New Delhi", "Delhi"
    ],

    "Jammu and Kashmir": [
        "Srinagar", "Jammu", "Anantnag", "Baramulla"
    ],

    "Ladakh": [
        "Leh", "Kargil"
    ],

    "Puducherry": [
        "Puducherry", "Karaikal"
    ],

    "Chandigarh": [
        "Chandigarh"
    ]
}


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
@login_required(login_url="login")
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

        email = request.user.email.strip()

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
        # Professional field validation
        # -------------------------

        # Name: letters, spaces, dot, apostrophe, hyphen only
        if not re.fullmatch(r"[A-Za-zÀ-ÿ .'-]{2,100}", full_name):
            messages.error(
                request,
                "Please enter a valid full name."
            )
            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # Phone: Indian 10 digit mobile number
        if not re.fullmatch(r"[6-9][0-9]{9}", phone):
            messages.error(
                request,
                "Please enter a valid 10-digit Indian mobile number."
            )
            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # PIN Code: exactly 6 digits and cannot start with 0
        if not re.fullmatch(r"[1-9][0-9]{5}", pin_code):
            messages.error(
                request,
                "Please enter a valid 6-digit PIN code."
            )
            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )
        # =====================================================
        # STATE + CITY VALIDATION
        # =====================================================

        STATE_CITIES = {

            "Andhra Pradesh": [
                "Visakhapatnam",
                "Vijayawada",
                "Guntur",
                "Nellore",
                "Tirupati",
                "Kurnool",
            ],

            "Arunachal Pradesh": [
                "Itanagar",
                "Naharlagun",
                "Pasighat",
                "Tawang",
            ],

            "Assam": [
                "Guwahati",
                "Dibrugarh",
                "Jorhat",
                "Silchar",
                "Tezpur",
            ],

            "Bihar": [
                "Patna",
                "Gaya",
                "Muzaffarpur",
                "Bhagalpur",
                "Darbhanga",
            ],

            "Chhattisgarh": [
                "Raipur",
                "Bhilai",
                "Bilaspur",
                "Korba",
                "Durg",
            ],

            "Goa": [
                "Panaji",
                "Margao",
                "Vasco da Gama",
                "Mapusa",
            ],

            "Gujarat": [
                "Ahmedabad",
                "Surat",
                "Vadodara",
                "Rajkot",
                "Bhavnagar",
                "Jamnagar",
            ],

            "Haryana": [
                "Gurugram",
                "Faridabad",
                "Panipat",
                "Ambala",
                "Hisar",
                "Karnal",
            ],

            "Himachal Pradesh": [
                "Shimla",
                "Manali",
                "Dharamshala",
                "Solan",
                "Mandi",
            ],

            "Jharkhand": [
                "Ranchi",
                "Jamshedpur",
                "Dhanbad",
                "Bokaro",
                "Deoghar",
            ],

            "Karnataka": [
                "Bengaluru",
                "Mysuru",
                "Mangaluru",
                "Hubballi",
                "Belagavi",
                "Dharwad",
            ],

            "Kerala": [
                "Thiruvananthapuram",
                "Kochi",
                "Kozhikode",
                "Thrissur",
                "Kollam",
                "Kannur",
            ],

            "Madhya Pradesh": [
                "Bhopal",
                "Indore",
                "Gwalior",
                "Jabalpur",
                "Ujjain",
                "Sagar",
            ],

            "Maharashtra": [
                "Mumbai",
                "Pune",
                "Nagpur",
                "Nashik",
                "Thane",
                "Aurangabad",
                "Kolhapur",
            ],

            "Manipur": [
                "Imphal",
                "Thoubal",
                "Bishnupur",
            ],

            "Meghalaya": [
                "Shillong",
                "Tura",
                "Jowai",
            ],

            "Mizoram": [
                "Aizawl",
                "Lunglei",
                "Champhai",
            ],

            "Nagaland": [
                "Kohima",
                "Dimapur",
                "Mokokchung",
            ],

            "Odisha": [
                "Bhubaneswar",
                "Cuttack",
                "Rourkela",
                "Puri",
                "Berhampur",
                "Sambalpur",
            ],

            "Punjab": [
                "Amritsar",
                "Ludhiana",
                "Jalandhar",
                "Patiala",
                "Bathinda",
            ],

            "Rajasthan": [
                "Jaipur",
                "Jodhpur",
                "Udaipur",
                "Kota",
                "Ajmer",
                "Bikaner",
            ],

            "Sikkim": [
                "Gangtok",
                "Namchi",
                "Gyalshing",
            ],

            "Tamil Nadu": [
                "Chennai",
                "Coimbatore",
                "Madurai",
                "Salem",
                "Tiruchirappalli",
                "Tirunelveli",
                "Vellore",
            ],

            "Telangana": [
                "Hyderabad",
                "Warangal",
                "Nizamabad",
                "Karimnagar",
                "Khammam",
            ],

            "Tripura": [
                "Agartala",
                "Udaipur",
                "Dharmanagar",
            ],

            "Uttar Pradesh": [
                "Lucknow",
                "Kanpur",
                "Agra",
                "Varanasi",
                "Prayagraj",
                "Ghaziabad",
                "Noida",
                "Meerut",
                "Gorakhpur",
                "Bareilly",
            ],

            "Uttarakhand": [
                "Dehradun",
                "Haridwar",
                "Rishikesh",
                "Nainital",
                "Haldwani",
                "Roorkee",
            ],

            "West Bengal": [
                "Kolkata",
                "Howrah",
                "Durgapur",
                "Siliguri",
                "Asansol",
            ],

            "Delhi": [
                "New Delhi",
                "Delhi",
            ],

            "Jammu and Kashmir": [
                "Srinagar",
                "Jammu",
                "Anantnag",
                "Baramulla",
            ],

            "Ladakh": [
                "Leh",
                "Kargil",
            ],
        }


        # State must be from our list
        if state not in STATE_CITIES:

            messages.error(
                request,
                "Please select a valid state."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )


        # City must belong to selected state
        if city not in STATE_CITIES[state]:

            messages.error(
                request,
                "Please select a valid city for the selected state."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                }
            )

        # Address: minimum 10 characters
        if len(address) < 10 or len(address) > 500:
            messages.error(
                request,
                "Please enter a valid complete address."
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

    admin_email = os.environ.get("ADMIN_EMAIL")

    items_text = "\n".join(
        [
            f"- {item.product_name} x {item.quantity} = ₹{item.total}"
            for item in order.items.all()
        ]
    )

    # =====================================================
    # CUSTOMER EMAIL
    # =====================================================

    customer_subject = (
        f"ShopEasy Garden - Order {order.order_number} Confirmed"
    )

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

Thank you for shopping with ShopEasy Garden.
"""

    try:
        sent = send_customer_email(
            to_email=order.customer_email,
            subject=customer_subject,
            message=customer_message,
        )

        if sent:
            print(
                f"CONFIRMATION EMAIL SENT: "
                f"{order.customer_email}"
            )
        else:
            print(
                f"CONFIRMATION EMAIL FAILED: "
                f"{order.customer_email}"
            )

    except Exception as e:
        print(
            "CUSTOMER EMAIL ERROR:",
            repr(e)
        )

    # =====================================================
    # ADMIN EMAIL
    # =====================================================

    if admin_email:

        admin_subject = (
            f"New ShopEasy Garden Order - "
            f"{order.order_number}"
        )

        admin_message = f"""New order received.

Order Number:
{order.order_number}

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
            sent = send_customer_email(
                to_email=admin_email,
                subject=admin_subject,
                message=admin_message,
            )

            if sent:
                print(
                    f"ADMIN EMAIL SENT: "
                    f"{admin_email}"
                )
            else:
                print(
                    f"ADMIN EMAIL FAILED: "
                    f"{admin_email}"
                )

        except Exception as e:
            print(
                "ADMIN EMAIL ERROR:",
                repr(e)
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

# =========================================================
# MY ORDERS
# =========================================================

def my_orders(request):

    if not request.user.is_authenticated:
        messages.info(
            request,
            "Please login to view your orders."
        )
        return redirect("login")

    orders = Order.objects.filter(
        customer_email__iexact=request.user.email
    ).prefetch_related("items")

    return render(
        request,
        "store/my_orders.html",
        {
            "orders": orders,
        }
    )

@login_required
def profile(request):
    return render(request, "store/profile.html")
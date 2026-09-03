from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q

from .models import Product, Category


def home(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    category_slug = request.GET.get("category", "").strip()

    if category_slug:
        products = products.filter(
            category__slug=category_slug
        )

    context = {
        "products": products,
        "categories": categories,
        "query": query,
        "selected_category": category_slug,
    }

    return render(request, "store/home.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_available=True
    )

    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(
        id=product.id
    )[:4]

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "related_products": related_products,
        }
    )


def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    cart = request.session.get("cart", {})
    product_id = str(product.id)

    current_quantity = cart.get(product_id, 0)

    if current_quantity < product.stock:
        cart[product_id] = current_quantity + 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def cart(request):
    cart_data = request.session.get("cart", {})

    cart_items = []
    subtotal = 0

    for product_id, quantity in cart_data.items():
        product = Product.objects.filter(
            id=product_id,
            is_available=True
        ).first()

        if product:
            total = product.price * quantity
            subtotal += total

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "total": total,
            })

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total": subtotal,
    }

    return render(request, "store/cart.html", context)


def update_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    quantity = int(request.POST.get("quantity", 1))

    cart_data = request.session.get("cart", {})
    product_id = str(product.id)

    if quantity <= 0:
        cart_data.pop(product_id, None)
    else:
        cart_data[product_id] = min(quantity, product.stock)

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def remove_from_cart(request, product_id):
    cart_data = request.session.get("cart", {})

    cart_data.pop(str(product_id), None)

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")
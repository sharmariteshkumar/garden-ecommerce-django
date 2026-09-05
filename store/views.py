from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import Product, Category


def store_home(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    context = {
        "products": products,
        "categories": categories,
    }

    return render(request, "store/home.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_available=True
    )

    return render(
        request,
        "store/product_detail.html",
        {"product": product}
    )


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    quantity = int(request.POST.get("quantity", 1))

    if quantity < 1:
        quantity = 1

    if product.stock < 1:
        return redirect("store_home")

    cart = request.session.get("cart", {})

    product_id = str(product.id)
    current_quantity = int(cart.get(product_id, 0))

    new_quantity = current_quantity + quantity

    # Stock se zyada add nahi hone dena
    if new_quantity > product.stock:
        new_quantity = product.stock

    cart[product_id] = new_quantity

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def cart(request):
    cart_data = request.session.get("cart", {})

    products = Product.objects.filter(
        id__in=cart_data.keys(),
        is_available=True
    )

    cart_items = []
    total = Decimal("0.00")

    for product in products:
        quantity = int(cart_data.get(str(product.id), 0))

        if quantity <= 0:
            continue

        # Stock change hone par quantity ko stock ke andar rakho
        if quantity > product.stock:
            quantity = product.stock
            cart_data[str(product.id)] = quantity

        item_total = product.price * quantity
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


@require_POST
def update_cart(request, product_id):

    if request.method == "POST":

        quantity = int(request.POST.get("quantity", 1))

        cart = request.session.get("cart", {})

        product_id = str(product_id)

        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("cart")


@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})

    product_id = str(product_id)

    cart.pop(product_id, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def all_products(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    sort = request.GET.get('sort', '')

    # Search Filter
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Category Filter
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Sorting Filter
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/all_products.html', context)
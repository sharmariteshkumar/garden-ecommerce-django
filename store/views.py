from django.shortcuts import render, get_object_or_404
from .models import Product, Category


def home(request):
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
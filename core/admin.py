from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    search_fields = (
        "name",
    )


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
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    list_editable = (
        "price",
        "stock",
        "is_available",
    )
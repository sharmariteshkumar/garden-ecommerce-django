import json
from pathlib import Path

from django.core import serializers
from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Category, Product


class Command(BaseCommand):
    help = "Import initial plants only when the database is empty"

    def handle(self, *args, **options):
        if Product.objects.exists() or Category.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Products/categories already exist. Skipping plant import."
                )
            )
            return

        fixture_path = Path("plant_product.json")

        if not fixture_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    "plant_product.json not found in project root."
                )
            )
            return

        with open(fixture_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        with transaction.atomic():
            for obj in serializers.deserialize(
                "json",
                json.dumps(data)
            ):
                obj.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Initial plants imported successfully."
            )
        )
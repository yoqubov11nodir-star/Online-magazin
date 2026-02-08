from django.contrib import admin

from .models import Category, Product, ProductImages

admin.site.register([Category, Product, ProductImages])

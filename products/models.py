from django.db import models

class Category(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precent = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    main_image = models.ImageField(upload_to='products/', null=True, blank=True) # Shu joyiga null=True qo'shing

    def __str__(self):
        return self.title

class ProductImages(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")

    def __str__(self):
        return self.product.title

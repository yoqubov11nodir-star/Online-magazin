from django.shortcuts import render
from django.views import View

from products.models import Category, Product
from users.models import Cart

class HomeView(View):
    def get(self, request):
        categories = Category.objects.all()
        products = Product.objects.all().order_by('-id')[:4]

        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)
            total_price = sum(item.total_price for item in cart_items)
        else:
            cart_items = []
            total_price = 0

        return render(request, 'index.html', {
            'categories': categories,
            'products': products,
            'total_price': total_price
        })

class ProductsView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'products.html', {
            "products":products
        })
    
class ProductDetailView(View):
    def get(self, request, id):
        product = Product.objects.get(id=id)
        images = product.images.all()

        releted_products = Product.objects.filter(
            category=product.category,
        ).exclude(id=product.id)[:3]

        discount = product.discount_price if product.discount_price else None

        return render(request, 'shop-details.html', {
            "product":product,
            'images':images,
            'releted_products':releted_products,
            'discount': discount
        })
    

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

class CartView(LoginRequiredMixin, View):
    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        total_price = sum(item.total_price for item in cart_items)
        return render(request, 'shop-cart.html', {
            'cart_items': cart_items,
            'total_price': total_price
        })

class AddToCartView(LoginRequiredMixin, View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        return redirect('cart')
    

import random
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.views.generic import ListView

from .models import User, EmailVerify, Cart, Order, OrderItem, WishList
from products.models import Product, Category 

class RegisterView(View):
    def get(self, request):
        return render(request, 'auth/register.html')

    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password']
        password2 = request.POST['confirm_password']

        if User.objects.filter(username=username).exists():
            return render(request, 'auth/register.html', {"error":"Bu username band"})

        if password1 != password2:
            return render(request, 'auth/register.html', {"error": "Parollar mos emas"})

        if User.objects.filter(email=email).exists():
            return render(request, 'auth/register.html', {"error": "Bu email ishlatilgan"})

        User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            is_active=False
        )
        code = str(random.randint(100000, 999999))
        send_mail(
            "Tasdiqlash kodi",
            f"Sizning tasdiqlash kodingiz {code}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        email_verify = EmailVerify.objects.create(email=email, code=code)
        request.session['email'] = email
        return redirect('email_verify')

class EmailVerifyView(View):
    def get(self, request):
        return render(request, 'auth/email_verify.html')

    def post(self, request):
        confirm_code = request.POST['code']
        email = request.session.get('email')
        email_verify = EmailVerify.objects.filter(email=email, is_confirmed=False).order_by('-id').first()

        if confirm_code != email_verify.code:
            return render(request, 'auth/email_verify.html', {"error": "Tasdiqlash kodi xato"})  

        now = timezone.now()
        if now > email_verify.expiration_time:
            return render(request, 'auth/email_verify.html', {"error": "Kodni yaroqli muddati tugagan"})

        email_verify.is_confirmed = True
        email_verify.save()
        user = User.objects.get(email=email)
        user.is_active = True
        user.save()
        request.session.flush()
        return redirect('login')

class LoginView(View):
    def get(self, request):
        return render(request, 'auth/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user_obj = User.objects.filter(username=username).first()
        if user_obj:
            if not user_obj.is_active:
                request.session['email'] = user_obj.email
                return redirect('email_verify')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                # MANA SHU YERNI O'ZGARTIRDIK:
                return redirect('home') # Login bo'lgach do'kon sahifasiga o'tadi
            else:
                return render(request, 'auth/login.html', {"error": "Parol noto'g'ri"})
        else:
            return render(request, 'auth/login.html', {"error": "Foydalanuvchi topilmadi"})

def add_to_cart(request, id):
    product = Product.objects.get(id=id)
    quantity = int(request.POST.get("quantity", 1))
    cart_item = Cart.objects.filter(user=request.user, product=product).first()
    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        Cart.objects.create(user=request.user, product=product, quantity=quantity)
    return redirect('shop-cart')

def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('home')
    total_price = sum(item.total_price for item in cart_items)
    balance = request.user.balance if request.user.balance else Decimal('0.00')
    if balance < total_price:
        messages.error(request, "Mablag' yetarli emas!")
        return redirect('shop-cart')
    for item in cart_items:
        if item.product.stock < item.quantity:
            messages.error(request, f"{item.product.title} yetarli emas!")
            return redirect('shop-cart')
    order = Order.objects.create(user=request.user)
    for item in cart_items:
        product = item.product
        product.stock -= item.quantity
        product.save()
        OrderItem.objects.create(order=order, product=product, quantity=item.quantity, price=product.price)
    request.user.balance -= total_price
    request.user.save()
    cart_items.delete()
    messages.success(request, "Xarid muvaffaqiyatli yakunlandi!")
    return redirect('home')

class ShopCartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)
            subtotal = sum(item.total_price for item in cart_items)
            total_price = subtotal
        else:
            cart_items, subtotal, total_price = [], 0, 0
        return render(request, 'shop-cart.html', {'cart_items': cart_items, 'subtotal': subtotal, 'total_price': total_price})

class CartDeleteView(View):
    def post(self, request, id):
        cart_item = Cart.objects.filter(id=id, user=request.user).first()
        if cart_item:
            cart_item.delete()
        return redirect('shop-cart')

class CartUpdateView(View):
    def post(self, request, id):
        cart_item = Cart.objects.filter(id=id, user=request.user).first()
        if not cart_item:
            return redirect('shop-cart')
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            cart_item.delete()
        elif quantity > cart_item.product.stock:
            cart_item.quantity = cart_item.product.stock
            cart_item.save()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        return redirect('shop-cart')

class WishListView(ListView):
    model = WishList
    template_name = 'wishlist.html'
    context_object_name = 'wishlist_items'
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return WishList.objects.filter(user=self.request.user)
        return WishList.objects.none() 

class ShopListView(ListView):
    model = Product
    template_name = 'shop-list.html'
    context_object_name = 'products'
    def get_queryset(self):
        return self.model.objects.all().order_by('-id')

def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    my_products = Product.objects.filter(author=request.user)
    return render(request, 'profile.html', {'products': my_products})

def product_add(request):
    categories = Category.objects.all()
    if request.method == "POST":
        Product.objects.create(
            author=request.user,
            title=request.POST.get('title'),
            price=request.POST.get('price'),
            stock=request.POST.get('stock'),
            precent=request.POST.get('percent', 0) or 0, # HTML dagi name="percent"
            discount_price=request.POST.get('discount', 0) or 0, # HTML dagi name="discount"
            category_id=request.POST.get('category'),
            main_image=request.FILES.get('image')
        )
        return redirect('profile')
    return render(request, 'product_form.html', {'categories': categories})

def product_delete(request, id):
    product = get_object_or_404(Product, id=id, author=request.user)
    product.delete()
    return redirect('profile')

def product_update(request, id):
    product = get_object_or_404(Product, id=id, author=request.user)
    categories = Category.objects.all()
    if request.method == "POST":
        product.title = request.POST.get('title')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        cat_id = request.POST.get('category')
        product.category = Category.objects.get(id=cat_id)
        if request.FILES.get('image'):
            product.main_image = request.FILES.get('image')
        product.save()
        return redirect('profile')
    return render(request, 'product_form.html', {'product': product, 'categories': categories})
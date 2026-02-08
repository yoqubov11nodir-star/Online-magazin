from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View

from django.conf import settings
from django.core.mail import send_mail

import random
from .models import *
from decimal import Decimal

class RegisterView(View):
    def get(self, request):
        return render(request, 'auth/register.html')

    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password']
        password2 = request.POST['confirm_password']

        if User.objects.filter(username=username).exists():
            return render(request, 'auth/register.html', {
                "error":"Bu username band"
            })

        if password1 != password2:
            return render(request, 'auth/register.html', {
                "error": "Parollar mos emas"
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'auth/register.html', {
                "error": "Bu email ishlatilgan"
            })

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

        email_verify = EmailVerify.objects.create(
            email=email,
            code=code,
        )
        email_verify.save()

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
            return render(request, 'auth/email_verify.html', {
                "error": "Tasdiqlash kodi xato"
            })  

        now = timezone.now()
        if now > email_verify.expiration_time:
            return render(request, 'auth/email_verify.html', {
                "error": "Kodni yaroqli muddati tugagan"
            })

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

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'auth/login.html', {
                "error": "Username yoki parol xato kiritildi"
            })


def add_to_cart(request, id):
    product = Product.objects.get(id=id)
    quantity = int(request.POST.get("quantity", 1))

    cart_item = Cart.objects.filter(user=request.user, product=product).first()
    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        Cart.objects.create(
            user=request.user,
            product=product,
            quantity=quantity
        )

    return redirect('shop-cart')


def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('home')

    total_price = sum(item.total_price for item in cart_items)
    
    balance = request.user.balance if request.user.balance is not None else Decimal('0.00')

    if balance < total_price:
        return redirect('home')

    order = Order.objects.create(
        user=request.user
    )
    for item in cart_items:
        OrderItem.objects.create(
            product=item.product,
            order = order,
            quantity=item.quantity,
            price=item.product.price
        )

    request.user.balance = balance - total_price
    request.user.save()

    cart_items.delete()
    return redirect('home')


class AddToCartView(View):
    def post(self, request, id):
        product = Product.objects.get(id=id)
        quantity = int(request.POST.get("quantity", 1))

        if quantity > product.stock:
            return redirect('home')

        cart_item = Cart.objects.filter(user=request.user, product=product).first()
        if cart_item:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                cart_item.quantity = product.stock
            cart_item.save()
        else:
            Cart.objects.create(
                user=request.user,
                product=product,
                quantity=quantity
            )

        return redirect('shop-cart')

class ShopCartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            # Foydalanuvchiga tegishli barcha savat elementlarini olish
            cart_items = Cart.objects.filter(user=request.user)
            # Jami summani hisoblash
            subtotal = sum(item.total_price for item in cart_items)
            total_price = subtotal # Agar kupon bo'lmasa total subtotalga teng
        else:
            cart_items = []
            subtotal = 0
            total_price = 0

        return render(request, 'shop-cart.html', {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'total_price': total_price
        })

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

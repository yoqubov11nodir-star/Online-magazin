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

from .models import User, EmailVerify, Cart, Order, OrderItem, WishList, Comment, Message
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
                return redirect('shop-list') # Login bo'lgach do'kon sahifasiga o'tadi
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
    # Agar foydalanuvchi kirmagan bo'lsa login sahifasiga
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)
    
    # Savatcha bo'sh bo'lsa shopga qaytarish
    if not cart_items:
        messages.info(request, "Savatchangiz bo'sh")
        return redirect('shop-list')

    total_price = sum(item.total_price for item in cart_items)
    balance = request.user.balance if request.user.balance else Decimal('0.00')

    # Mablag' tekshiruvi
    if balance < total_price:
        messages.error(request, "Mablag' yetarli emas!")
        return redirect('shop-cart')

    # Ombor tekshiruvi
    for item in cart_items:
        if item.product.stock < item.quantity:
            messages.error(request, f"{item.product.title} mahsulotidan omborda yetarli emas!")
            return redirect('shop-cart')

    # Buyurtma yaratish
    order = Order.objects.create(user=request.user)
    for item in cart_items:
        product = item.product
        product.stock -= item.quantity
        product.save()
        OrderItem.objects.create(
            order=order, 
            product=product, 
            quantity=item.quantity, 
            price=product.price
        )

    # Balansdan ayirish
    request.user.balance -= total_price
    request.user.save()

    # Savatchani tozalash
    cart_items.delete()
    
    messages.success(request, "Xarid muvaffaqiyatli yakunlandi!")
    return redirect('shop-list') # Xarid tugagach shop-listga qaytadi

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
        # 1. Dastlab barcha mahsulotlarni oxirgi qo'shilgan tartibda olamiz
        queryset = super().get_queryset().order_by('-id')
        
        # 2. URL'dan 'q' parametrini qidiramiz (masalan: /shop/?q=kitob)
        query = self.request.GET.get('q')
        
        if query:
            # 3. Agar so'rov bo'lsa, title bo'yicha filtrlaymiz
            queryset = queryset.filter(title__icontains=query)
            
        return queryset

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

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'product-detail.html', {'product': product})

def add_comment(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        text = request.POST.get('comment_text')
        is_private = request.POST.get('is_private')
        
        comment = Comment.objects.create(
            product=product,
            user=request.user,
            text=text,
            is_public=False if is_private else True
        )

        # AGAR SHAXSIY BO'LSA, CHATGA XABAR YUBORISH
        if is_private:
            Message.objects.create(
                sender=request.user,
                receiver=product.author, # Mahsulot egasiga boradi
                text=f"Yangi shaxsiy izoh: {text}"
            )
            
        return redirect('product-detail')
    

from django.db.models import Q
from django.http import JsonResponse

# 1. Chatlar ro'yxati (Kim bilan yozishgan bo'lsa o'shalar chiqadi)
def chat_list(request):
    messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
    chat_users = set()
    for msg in messages:
        chat_users.add(msg.receiver if msg.sender == request.user else msg.sender)
    return render(request, 'chat_list.html', {'chat_users': chat_users})

# 2. Ma'lum bir odam bilan chat sahifasi
def chat_detail(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) | 
        (Q(sender=other_user) & Q(receiver=request.user))
    )
    return render(request, 'chat_detail.html', {'other_user': other_user, 'messages': messages})

# 3. Xabar yuborish (AJAX orqali)
def send_message(request):
    if request.method == "POST":
        receiver_id = request.POST.get('receiver_id')
        text = request.POST.get('text')
        receiver = get_object_or_404(User, id=receiver_id)
        
        # Bu yerda Message modelini aniq ko'rsatamiz
        msg = Message.objects.create(
            sender=request.user, 
            receiver=receiver, 
            text=text
        )
        return JsonResponse({
            'status': 'ok', 
            'text': msg.text, 
            'sender': msg.sender.username
        })
    
# Komentariyani o'chirish
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Faqat izoh egasi o'chira olishi uchun
    if comment.user == request.user:
        comment.delete()
    return redirect('shop-list')

# Komentariyani tahrirlash (Update)
def update_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    if request.method == "POST":
        new_text = request.POST.get('comment_text')
        if new_text:
            comment.text = new_text
            comment.save()
        # Qat'iy ravishda product-detail ga qaytarish
        return redirect('product-detail', id=comment.product.id)
    
    # Agar GET bo'lsa ham (aslida modalda GET kerak emas), detail sahifasiga qaytadi
    return redirect('product-detail', id=comment.product.id)

def add_to_wishlist(request, product_id):
    # 1. Agar foydalanuvchi tizimga kirmagan bo'lsa
    if not request.user.is_authenticated:
        return redirect('login')  # 'login' - sizdagi login url nomi bo'lishi kerak

    # 2. Agar foydalanuvchi kirgan bo'lsa
    product = get_object_or_404(Product, id=product_id)
    
    # Mahsulotni wishlistga qo'shish (agar allaqachon bo'lsa, shunchaki get qiladi)
    WishList.objects.get_or_create(user=request.user, product=product)
    
    # Kelgan sahifasiga qaytarish
    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))

def remove_from_wishlist(request, item_id):
    # WishList modelidan ID bo'yicha topib o'chiramiz
    wishlist_item = get_object_or_404(WishList, id=item_id, user=request.user)
    wishlist_item.delete()
    return redirect('wishlist')
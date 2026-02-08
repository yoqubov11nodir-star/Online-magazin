from django.urls import path

from . import views
from . views import AddToCartView, ShopCartView, CartDeleteView, CartUpdateView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('email-verify/', views.EmailVerifyView.as_view(), name='email_verify'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('checkout/', views.checkout, name='checkout'),
    path('add_to_cart/<int:id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('shop-cart/', ShopCartView.as_view(), name='shop-cart'),
    path('cart/delete/<int:id>/', views.CartDeleteView.as_view(), name='cart_delete'),
    path('cart/update/<int:id>/', views.CartUpdateView.as_view(), name='cart_update'),

]

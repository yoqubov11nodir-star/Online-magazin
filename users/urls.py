from django.urls import path
from . import views 
from .views import checkout

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('email-verify/', views.EmailVerifyView.as_view(), name='email_verify'),
    path('', views.LoginView.as_view(), name='login'), 

    # Profile & Products
    path('profile/', views.profile_view, name='profile'),
    path('profile/add/', views.product_add, name='product_add'),
    path('profile/update/<int:id>/', views.product_update, name='product_update'),
    path('profile/delete/<int:id>/', views.product_delete, name='product_delete'),
    
    # Shop & Wishlist
    path('shop-list/', views.ShopListView.as_view(), name='shop-list'),
    path('shop-cart/', views.ShopCartView.as_view(), name='shop-cart'),
    path('wishlist/', views.WishListView.as_view(), name='wishlist'),

    # Cart Actions 
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart-update/<int:id>/', views.CartUpdateView.as_view(), name='cart_update'),
    path('cart-delete/<int:id>/', views.CartDeleteView.as_view(), name='cart_delete'),
    
    # Order
    path('checkout/', checkout, name='checkout'),
]
from django.urls import path
from . import views 
from .views import checkout

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('email-verify/', views.EmailVerifyView.as_view(), name='email_verify'),
    path('', views.LoginView.as_view(), name='login'), 

    # Profile and Products
    path('profile/', views.profile_view, name='profile'),
    path('profile/add/', views.product_add, name='product_add'),
    path('profile/update/<int:id>/', views.product_update, name='product_update'),
    path('profile/delete/<int:id>/', views.product_delete, name='product_delete'),
    
    # Shop and Wishlist
    path('wishlist/', views.WishListView.as_view(), name='wishlist'),
    path('shop-list/', views.ShopListView.as_view(), name='shop-list'),
    path('shop-cart/', views.ShopCartView.as_view(), name='shop-cart'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Cart Actions 
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart-update/<int:id>/', views.CartUpdateView.as_view(), name='cart_update'),
    path('cart-delete/<int:id>/', views.CartDeleteView.as_view(), name='cart_delete'),
    
    # Order
    path('checkout/', checkout, name='checkout'),

    path('product/<int:id>/', views.product_detail, name='product-detail'),
    path('add-comment/<int:product_id>/', views.add_comment, name='add_comment'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('update-comment/<int:comment_id>/', views.update_comment, name='update_comment'),

    # Chat
    path('chats/', views.chat_list, name='chat-list'),
    path('chat/<int:user_id>/', views.chat_detail, name='chat-detail'),
    path('send-message/', views.send_message, name='send-message'),

]   
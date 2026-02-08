from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductsView.as_view(), name='products'),
    path('product/<int:id>/detail/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # YANGI QATORLAR:
    path('cart/', views.CartView.as_view(), name='cart'),
    path('add-to-cart/<int:product_id>/', views.AddToCartView.as_view(), name='add-to-cart'),
]
from django.contrib import admin

from django.contrib import admin
from .models import Coupon

from .models import *

admin.site.register([User, EmailVerify, WishList,
                     Cart, Order, OrderItem])


admin.site.register(Coupon)


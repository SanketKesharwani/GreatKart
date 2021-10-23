from django.contrib import admin
from .models import Payment,Order,OrderProduct
# Register your models here.

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra  = 0

admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(OrderProduct)

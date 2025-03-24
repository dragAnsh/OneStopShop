from django.contrib import admin
from .models import ShippingAddress, Order, OrderItem


admin.site.register(ShippingAddress)
admin.site.register(OrderItem)

class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0

# Extend the Order Model
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    readonly_fields = ('date_ordered', )

admin.site.register(Order, OrderAdmin)
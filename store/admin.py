from django.contrib import admin
from .models import Category, Product, Profile
from django.contrib.auth.models import User
from payment.models import ShippingAddress


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Profile)

# The admin interface has the ability to edit models on the same page as a parent model. These are called inlines
# Django provides two subclasses of InlineModelAdmin and they are: 1. TabularInline, 2. StackedInline. The difference between these two is merely the template used to render them.
# Mixes Profile Info and User Info
class ProfileInline(admin.StackedInline):
    model = Profile # The model which the inline is using. This is required. Profile will be inlined inside User Model

class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0

# Extend the User Model
class UserAdmin(admin.ModelAdmin):
    inlines = [ProfileInline, ShippingAddressInline]

# removes the default way Django displays the User model in the admin panel.
admin.site.unregister(User)
# register our custom UserAdmin
admin.site.register(User, UserAdmin)
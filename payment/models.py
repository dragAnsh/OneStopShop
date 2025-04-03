from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now # this respects django's timezone settings in settings.py file. datetime will always give system time
from store.models import Product


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # one user can have multiple shipping addresses thus ForeignKey and not OneToOne Field
    shipping_phone = models.CharField(max_length=10)
    shipping_full_name = models.CharField(max_length=200)
    shipping_email = models.EmailField(max_length=200)
    shipping_address1 = models.CharField(max_length=200)
    shipping_address2 = models.CharField(max_length=200, null=True, blank=True)
    shipping_city = models.CharField(max_length=200)
    shipping_state = models.CharField(max_length=200, null=True, blank=True)
    shipping_zipcode = models.CharField(max_length=200, null=True, blank=True)
    shipping_country = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Shipping Address"

    def __str__(self):
        return f"Shipping Address - {str(self.id)}"
    

def create_shipping_address(sender, instance, created, **kwargs):
    if created:
        user_shipping_address = ShippingAddress(user=instance)
        user_shipping_address.save()


post_save.connect(create_shipping_address, sender=User)


# Create Order and Order Items Model
class Order(models.Model):
    payment_method_choices = {
        "PayPal": "PayPal",
        "Stripe": "Stripe",
        "COD": "Cash On Delivery",
        "NA": "NA"
    }

    order_status_choices = {
        "Pending": "Pending",
        "Processed": "Processed",
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # Logged In Users and Guests both can checkout: thus null=True
    # Add Shipping Details seperately so even if a User deletes ShippingAddress objects, we still have the record. Thus not making a ForeignKey. ??? IDK ACTUALLY. Because we are not allowing users to dlete their shipping addresses. I think it would be better to have FK instead of repeating the same info. CHECK LATER!!!
    shipping_full_name = models.CharField(max_length=200)
    shipping_phone = models.CharField(max_length=10)
    shipping_email = models.EmailField(max_length=200)
    shipping_address = models.TextField(max_length=2000) # contains Address, city, state, zipcode, country
    billing_full_name = models.CharField(max_length=200)
    billing_phone = models.CharField(max_length=10)
    billing_email = models.EmailField(max_length=200)
    billing_address = models.TextField(max_length=2000) # contains Address, city, state, zipcode, country
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_ordered = models.DateTimeField(auto_now_add=True)
    shipped = models.BooleanField(default=False)
    date_shipped = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default="Pending", choices=order_status_choices)
    invoice_id = models.CharField(max_length=36, blank=True)
    payment_method = models.CharField(max_length=6, choices=payment_method_choices)

    def __str__(self):
        return f"Order - {str(self.id)}"
    

# Auto Add shipping date if order is shipped
@receiver(pre_save, sender=Order) # we can use receiver decorator to connect or can use connect() method as well
def set_shipped_date_on_update(sender, instance, **kwargs):
    # Check if this is an existing order (not a new one)
    if instance.pk:  # Checks that instance is being updated and not created as Primary Key already exists. so instance.pk should not be None
        # Fetch the existing order from DB
        existing_order = sender.objects.get(pk=instance.pk) # instance is the object that is yet to be saved, so here the shipped will be true and existing_order will contain the old object that is fetched from DB and it should have shipped = False that means that we are updating shipped from False to True so we set date_shipped.

        # if instance.shipped and not existing_order.shipped: # If the shipped status is being updated to True
        old_shipped_status = existing_order.shipped
        new_shipped_status = instance.shipped

        if new_shipped_status == True and old_shipped_status == False:
            instance.date_shipped = now()

    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    total_price = models.DecimalField(default=0, max_digits=7, decimal_places=2)

    def __str__(self):
        return f"Order Item - {str(self.id)}"
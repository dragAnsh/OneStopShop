from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.conf import settings
from .models import Order, OrderItem
from .tasks import send_order_confirmation_email_task
from django.core.cache import cache
from django.contrib.auth.models import User


# Link the function to valid_ipn_received signal
@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    # Grab the info sent by PayPal
    ipn_object = sender

    if ipn_object.payment_status == ST_PP_COMPLETED:
        # Verify PayPal email
        if ipn_object.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
            return
        
        else:
            invoice_id = ipn_object.invoice
            
            # fetch Order data from cache
            order_data = cache.get(invoice_id)

            # if cache is expired
            if not order_data:
                return

            # Verify amount and currency
            if float(ipn_object.mc_gross) != order_data['amount_paid'] or ipn_object.mc_currency != 'USD':
                return
            
            # Create shipping address text from user_address_info
            include_fields = ("shipping_address1", "shipping_address2", "shipping_city", "shipping_state", "shipping_zipcode", "shipping_country")
            shipping_address = "\n".join(order_data['user_address_info'][field] for field in include_fields if order_data['user_address_info'].get(field))

            shipping_full_name = order_data['user_address_info']['shipping_full_name']
            shipping_email = order_data['user_address_info']['shipping_email']
            billing_full_name = order_data['user_address_info']['full_name']
            billing_email = order_data['user_address_info']['email']
            amount_paid = order_data['amount_paid']
            shipping_phone = order_data['user_address_info']['shipping_phone']
            billing_phone = order_data['user_address_info']['phone']

            # Fetch user object from ID (only if user exists)
            user_id = order_data['user']
            user = User.objects.get(id=user_id) if user_id else None

            # Create Billing Address Text from user_address_info
            include_fields = ("address1", "address2", "city", "state", "zipcode", "country")
            billing_address = "\n".join(order_data['user_address_info'][field] for field in include_fields if order_data['user_address_info'].get(field))

            # Create an order
            create_order = Order(user=user, shipping_full_name=shipping_full_name, shipping_phone=shipping_phone, shipping_email=shipping_email, billing_full_name=billing_full_name, billing_phone=billing_phone, billing_email=billing_email, shipping_address=shipping_address, billing_address=billing_address, amount_paid=amount_paid, invoice_id=invoice_id, payment_method = "PayPal")
            create_order.save()

            # Create Order Items
            order_items = []
            for product in order_data['products']:
                quantity = product['qty']
                price = product['sale_price'] if product['on_sale'] else product['price']
                total_price = product['total_price']
                
                create_order_item = OrderItem(order=create_order, product_id=product['id'], user=user, quantity=quantity, price=price, total_price=total_price)
                order_items.append(create_order_item)

            # Bulk Create to Optimize
            OrderItem.objects.bulk_create(order_items)

            cache.delete(invoice_id) #delete cache data after order has been created.

            # Send Emails Via Celery
            send_order_confirmation_email_task.delay(create_order.id)
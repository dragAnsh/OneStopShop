from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.conf import settings
from .models import Order
from .tasks import send_order_confirmation_email_task


# Link the function to valid_ipn_received signal
@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    # Grab the info sent by PayPal
    ipn_object = sender
    flagged_payment = False

    if ipn_object.payment_status == ST_PP_COMPLETED:
        # Verify PayPal email
        if ipn_object.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
            flagged_payment = True  # Invalid payment
        
        else:
            try:
                # fetch Order
                order = Order.objects.get(invoice_id=ipn_object.invoice)
            
                # Verify amount and currency
                if ipn_object.mc_gross != order.amount_paid or ipn_object.mc_currency != 'USD':
                    flagged_payment = True  # Invalid payment

                else:
                    # change order status from Pending to Paid
                    order.status = 'Processed'
                    # change payment method to PayPal from NA
                    order.payment_method = 'PayPal'
                    order.save()

                    # Send Emails Via Celery
                    send_order_confirmation_email_task.delay(order.id)
            except Exception as e:
                pass
    
    if flagged_payment:
        # Delete order if payment failed
        Order.objects.filter(invoice_id=ipn_object.invoice).delete()
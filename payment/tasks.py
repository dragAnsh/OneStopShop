from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import Order, OrderItem
from .models import Order, OrderItem
from django.db.models import Prefetch
from .utils import generate_invoice_pdf


@shared_task(name='order_confirmation_email')
def send_order_confirmation_email_task(user_order_id):
    """
    Sends an email for Order Confirmation with an HTML template and attaches an invoice PDF.
    :param user_order: Order instance
    """
    user_order = Order.objects.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).get(id=user_order_id)

    user_shipping_email = user_order.shipping_email
    user_billing_email = user_order.billing_email

    subject = f"{user_order.shipping_full_name}, Your OneStopShop Order#{user_order.id}: Invoice"
    text_content = render_to_string(
        "emails/order_confirmation_mail.txt",
        context={"user_order": user_order},
    )
    html_content = render_to_string(
        "emails/order_confirmation_mail.html",
        context={"user_order": user_order},
    )
    to = [user_shipping_email, user_billing_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Generate Invoice Data
    invoice_data = generate_invoice_pdf(user_order.id)
    msg.attach(f"{user_order.shipping_full_name}_order#{user_order.id}_invoice.pdf", invoice_data, "application/pdf")

    # Send Email
    msg.send()
    # To display result in Flower
    return f"Email sent to {user_shipping_email} and {user_billing_email}"


@shared_task(name='order_shipped_email')
def send_order_shipped_email_task(user_order_id):
    """
    Sends an email for Order Shipped Update with an HTML template and attaches an invoice PDF.
    :param user_order: Order instance
    """
    user_order = Order.objects.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).get(id=user_order_id)

    user_shipping_email = user_order.shipping_email
    user_billing_email = user_order.billing_email

    subject = f"{user_order.shipping_full_name}, Your OneStopShop Order#{user_order.id} has been Shipped!"
    text_content = render_to_string(
        "emails/order_shipped_mail.txt",
        context={"user_order": user_order},
    )
    html_content = render_to_string(
        "emails/order_shipped_mail.html",
        context={"user_order": user_order},
    )
    to = [user_shipping_email, user_billing_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Generate Invoice Data
    invoice_data = generate_invoice_pdf(user_order.id)
    msg.attach(f"{user_order.shipping_full_name}_order#{user_order.id}_invoice.pdf", invoice_data, "application/pdf")

    # Send Email
    msg.send()
    # To display result in Flower
    return f"Email sent to {user_shipping_email} and {user_billing_email}"


@shared_task(name='order_unshipped_email')
def send_order_unshipped_email_task(user_order_id):
    """
    Sends an email for Order Unshipped Update with an HTML template and attaches an invoice PDF.
    :param user_order: Order instance
    """
    user_order = Order.objects.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).get(id=user_order_id)

    user_shipping_email = user_order.shipping_email
    user_billing_email = user_order.billing_email

    subject = f"{user_order.shipping_full_name}, Update on Your OneStopShop Order#{user_order.id}"
    text_content = render_to_string(
        "emails/order_unshipped_mail.txt",
        context={"user_order": user_order},
    )
    html_content = render_to_string(
        "emails/order_unshipped_mail.html",
        context={"user_order": user_order},
    )
    to = [user_shipping_email, user_billing_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Generate Invoice Data
    invoice_data = generate_invoice_pdf(user_order.id)
    msg.attach(f"{user_order.shipping_full_name}_order#{user_order.id}_invoice.pdf", invoice_data, "application/pdf")

    # Send Email
    msg.send()
    # To display result in Flower
    return f"Email sent to {user_shipping_email} and {user_billing_email}"


@shared_task(name='user_registration_email')
def send_user_registration_email_task(user_email, first_name):
    """
    Sends an email to User for Successful Registration on the site with an HTML template.
    :param user_email: Email of User
    :param first_name: First Name of User
    """

    subject = f"{first_name}, Succesfully Registered on OneStopShop"
    text_content = render_to_string(
        "emails/user_registration_mail.txt",
        context={'user_email': user_email, 'first_name': first_name},
    )
    html_content = render_to_string(
        "emails/user_registration_mail.html",
        context={'user_email': user_email, 'first_name': first_name},
    )
    to = [user_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Send Email
    msg.send()
    # To display result in Flower
    return f"Email sent to {user_email}"
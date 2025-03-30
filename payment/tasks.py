from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import Order, OrderItem
from .models import Order, OrderItem
from django.db.models import Prefetch
from .utils import generate_invoice_pdf


@shared_task
def send_order_confirmation_email_task(user_order_id):
    """
    Sends an email for Order Confirmation with an HTML template and attaches an invoice PDF.
    :param user_order: Order instance
    """
    user_order = Order.objects.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).get(id=user_order_id)

    user_email = user_order.email
    subject = f"{user_order.full_name}, Your OneStopShop Order#{user_order.id}: Invoice"
    text_content = render_to_string(
        "emails/order_confirmation_mail.txt",
        context={"user_order": user_order},
    )
    html_content = render_to_string(
        "emails/order_confirmation_mail.html",
        context={"user_order": user_order},
    )
    to = [user_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Generate Invoice Data
    invoice_data = generate_invoice_pdf(user_order.id)
    msg.attach(f"{user_order.full_name}_order#{user_order.id}_invoice.pdf", invoice_data, "application/pdf")

    # Send Email
    msg.send()


@shared_task
def send_order_shipped_email_task(user_order_id):
    """
    Sends an email for Order Shipped Update with an HTML template and attaches an invoice PDF.
    :param user_order: Order instance
    """
    user_order = Order.objects.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).get(id=user_order_id)

    user_email = user_order.email
    subject = f"{user_order.full_name}, Your OneStopShop Order#{user_order.id} has been Shipped!"
    text_content = render_to_string(
        "emails/order_shipped_mail.txt",
        context={"user_order": user_order},
    )
    html_content = render_to_string(
        "emails/order_shipped_mail.html",
        context={"user_order": user_order},
    )
    to = [user_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Generate Invoice Data
    invoice_data = generate_invoice_pdf(user_order.id)
    msg.attach(f"{user_order.full_name}_order#{user_order.id}_invoice.pdf", invoice_data, "application/pdf")

    # Send Email
    msg.send()


@shared_task
def send_order_unshipped_email_task(user_order_id):
    """
    Sends an email for Order Unshipped Update with an HTML template and attaches an invoice PDF.
    :param user_order: Order instance
    """
    user_order = Order.objects.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).get(id=user_order_id)

    user_email = user_order.email
    subject = f"{user_order.full_name}, Update on Your OneStopShop Order#{user_order.id}"
    text_content = render_to_string(
        "emails/order_unshipped_mail.txt",
        context={"user_order": user_order},
    )
    html_content = render_to_string(
        "emails/order_unshipped_mail.html",
        context={"user_order": user_order},
    )
    to = [user_email]
    headers = {"List-Unsubscribe": "<mailto:updates.onestopshop@gmail.com>"}

    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=None, to=to, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"

    # Generate Invoice Data
    invoice_data = generate_invoice_pdf(user_order.id)
    msg.attach(f"{user_order.full_name}_order#{user_order.id}_invoice.pdf", invoice_data, "application/pdf")

    # Send Email
    msg.send()
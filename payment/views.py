from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from cart.cart import Cart
from store.forms import UserInfoForm
from store.models import Product, Profile
from .forms import ShippingForm, PaymentForm
from .models import ShippingAddress, Order, OrderItem
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.http import FileResponse
from io import BytesIO
from .models import Order, OrderItem
from django.db.models import Q, Prefetch
from .utils import generate_invoice_pdf
from .tasks import send_order_unshipped_email_task, send_order_confirmation_email_task, send_order_shipped_email_task
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
import uuid # unique user id for orders
from paypal.standard.forms import PayPalPaymentsForm


def generate_invoice(request, order_id):
    if not request.user.is_authenticated:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')

    pdf_data = generate_invoice_pdf(order_id)

    return FileResponse(BytesIO(pdf_data), as_attachment=True, filename=f"invoice_{order_id}.pdf")


def repeat_order(request, order_id):
    if request.user.is_authenticated:
        cart = Cart(request)
        # Grab OrderItems from the Order
        order_items = OrderItem.objects.filter(order=order_id)

        # Append Products to Cart
        for item in order_items:
            cart.add(item.product.id, item.quantity)

        # Review Your Cart and then Checkout
        messages.success(request, "Items added to your cart! Review before checkout.")
        return redirect('cart_summary')

    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def user_order_item(request, pk):
    if request.user.is_authenticated:
        item = get_object_or_404(OrderItem, id=pk)
        return render(request, 'payment/user_order_item.html', {'item': item})

    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def user_orders_list(request, filter):
    if request.user.is_authenticated:

        search_text = request.GET.get('search_text')
        # Query the Order Model
        user_orders = Order.objects.filter(user=request.user)
        
        if filter == "shipped":
            user_orders = user_orders.filter(shipped=True)
        elif filter == "unshipped":
            user_orders = user_orders.filter(shipped=False)

        # Use Prefetch to do a join on orderitem and product: Tackle (N+1) problem
        user_orders = user_orders.prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.select_related("product"))
        ).order_by("-date_ordered")

        if search_text:
            search_text = search_text.strip()
            user_orders = user_orders.filter(Q(orderitem__product__name__icontains=search_text)
                                             | Q(orderitem__product__category__name__icontains=search_text)
                                             | Q(orderitem__product__description__icontains=search_text)).distinct()
            
        user_orders = user_orders.order_by("-date_ordered")
        
        has_orders = True if user_orders.exists() else False

        # Pagination: Show 5 orders per page
        paginator = Paginator(user_orders, 5)
        page_number = request.GET.get("page")
        page_orders = paginator.get_page(page_number)

        return render(request, 'payment/user_orders_list.html', {'user_orders': page_orders, 'filter': filter, 'has_orders': has_orders})
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')
    

def user_order_detail(request, order_id):
    if request.user.is_authenticated:
        user_order = get_object_or_404(Order, id=order_id)
        user_order_items = OrderItem.objects.select_related("product").filter(order=user_order) # Use select_related for FK relationship:Tackle (N+1) problem
        return render(request, 'payment/user_order_detail.html', {'user_order': user_order, 'user_order_items': user_order_items})
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')
    

def mark_shipped(request, order_id):
    if request.user.is_authenticated and request.user.is_superuser and request.method=='POST':
        Order.objects.filter(id=order_id).update(shipped=True, date_shipped=now()) # calling update() thus pre_save doesn't trigger. for that to trigger use save() to update. or manually pass date_shipped like we are doing now
        messages.success(request, f"Order {order_id} Marked Shipped Successfully!")

        # Send Email to User using Celery + Redis
        send_order_shipped_email_task.delay(order_id)
        return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # return JsonResponse({})
        
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')
    

def mark_unshipped(request, order_id):
    if request.user.is_authenticated and request.user.is_superuser and request.method=='POST':
        Order.objects.filter(id=order_id).update(shipped=False, date_shipped=None)
        messages.success(request, f"Order {order_id} Marked Unshipped Successfully!")
        
        # Send Email to User using Celery + Redis
        send_order_unshipped_email_task.delay(order_id)
        return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # return JsonResponse({})

    else:
        messages.success(request, "ACCESS DENIED!")
        return redirect('home')


def order_item(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        item = get_object_or_404(OrderItem, id=pk)
        return render(request, 'payment/order_item.html', {'item': item})

    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        # get the order and order items
        order = get_object_or_404(Order, id=pk)
        order_items = OrderItem.objects.select_related("product").filter(order=order)

        return render(request, 'payment/orders.html', {'order': order, 'order_items': order_items})
    
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def shipped_dashboard(request):
    if request.user.is_authenticated and request.user.is_superuser:
        # only admin can access this page
        orders = Order.objects.filter(shipped=True).order_by("-date_ordered")

        # Pagination: Show 10 orders per page
        paginator = Paginator(orders, 10) # Django does not immediately split the queryset. Instead, it: 1. Stores the queryset (orders) internally. 2. Stores the number of objects per page (5). 3. Waits until you request a specific page to slice the queryset dynamically.
        page_number = request.GET.get("page")
        page_orders = paginator.get_page(page_number) # The method converts the page number to an integer. It calculates the start and end indices based on the page size. start = (2 - 1) * 10  # 10 end = start + 10  # 20. It slices the queryset dynamically like this: page_queryset = orders[10:20]  # Equivalent of LIMIT and OFFSET in SQL. It creates a Page object that holds this sliced queryset.

        return render(request, 'payment/shipped_dashboard.html', {'orders': page_orders})
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def not_yet_shipped_dashboard(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False).order_by("-date_ordered")

        # Pagination: Show 10 orders per page
        paginator = Paginator(orders, 10)
        page_number = request.GET.get("page")  # Get the page number from URL
        page_orders = paginator.get_page(page_number)

        return render(request, 'payment/not_yet_shipped_dashboard.html', {"orders": page_orders})
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def process_cod_order(request):
    if request.method=='POST':
        cart = Cart(request)
        user = request.user if request.user.is_authenticated else None

        # fetch invoice id
        invoice_id = request.POST['invoice_id']
            
        # fetch Order
        order = Order.objects.get(invoice_id=invoice_id)

        # mark order status to Success
        order.status = "Processed"
        order.payment_method = "COD"
        order.save()

        # Empty Shopping Cart From Session: Clear the cart dict from our 'cart' object
        cart.clear()

        # Empty Shopping Cart From DB
        if request.user.is_authenticated:
            Profile.objects.filter(user=user).update(old_cart="")

        # Send Order Confirmation Email: Use Celery as Distributed Task Queue and Redis as Message Broker 
        send_order_confirmation_email_task.delay(order.id)

        messages.success(request, "Order Placed!")
        return redirect('user_orders_list', {'filter': 'all'})
    
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def billing_info(request):
    if request.method=='POST':
        cart = Cart(request)
        products = cart.get_products()
        quantities = cart.get_quantities()

        for product in products:
            product.qty = quantities.get(str(product.id), 1)

            price = product.price
            if product.on_sale:
                price = product.sale_price

            product.total_price = (product.qty) * (price)

        cart_total = cart.cart_total()

        # Create a session with Shipping & Billing Info
        user_info_session = request.POST
        request.session['user_info'] = user_info_session

        host = request.get_host() # current domain/host serving the request
        invoice_id = str(uuid.uuid4())

        # Create PayPalPaymentsForm and paypal_dict
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': cart_total,
            'item_name': 'OneStopShop Order',
            'no_shipping': 2, # don't use PayPal Account's shipping address
            'invoice': invoice_id,
            'currency_code': 'USD',
            'notify_url': f'https://{host}{reverse("paypal-ipn")}',
            'return': f'https://{host}/{reverse("payment_success")}',
            'cancel_return': f'https://{host}{reverse("payment_failed", kwargs={'invoice_id': invoice_id})}',
        }

        # Create PayPal payments button
        paypal_form = PayPalPaymentsForm(initial=paypal_dict)

        # Create Order
        # Create Shipping Address Text from Session Info
        include_fields = ("shipping_address1", "shipping_address2", "shipping_city", "shipping_state", "shipping_zipcode", "shipping_country")
        shipping_address = "\n".join(user_info_session[field] for field in include_fields if user_info_session.get(field))

        shipping_full_name = user_info_session['shipping_full_name']
        shipping_email = user_info_session['shipping_email']
        billing_full_name = user_info_session['full_name']
        billing_email = user_info_session['email']
        amount_paid = cart_total
        user = request.user if request.user.is_authenticated else None
        shipping_phone = user_info_session['shipping_phone']
        billing_phone = user_info_session['phone']

        # Create Billing Address Text from Session Info
        include_fields = ("address1", "address2", "city", "state", "zipcode", "country")
        billing_address = "\n".join(user_info_session[field] for field in include_fields if user_info_session.get(field))

        # Create an order
        create_order = Order(user=user, shipping_full_name=shipping_full_name, shipping_phone=shipping_phone, shipping_email=shipping_email, billing_full_name=billing_full_name, billing_phone=billing_phone, billing_email=billing_email, shipping_address=shipping_address, billing_address=billing_address, amount_paid=amount_paid, status="Pending", invoice_id=invoice_id, payment_method="NA")
        create_order.save()
        # Create Order Items
        order_items = []
        for product in products:
            quantity = quantities.get(str(product.id), 1)
            price = product.sale_price if product.on_sale else product.price
            total_price = round(price * quantity, 2)
            
            create_order_item = OrderItem(order=create_order, product=product, user=user, quantity=quantity, price=price, total_price=total_price)
            order_items.append(create_order_item)
        
        # Bulk Create to Optimize
        OrderItem.objects.bulk_create(order_items)

        if request.user.is_authenticated:
            # Update the ShippingAddress & BillingAddress(profile info) for LoggedIn Users
            shipping_user = ShippingAddress.objects.get(user=request.user)
            shipping_form = ShippingForm(request.POST, instance=shipping_user)

            billing_user = Profile.objects.get(user=request.user)
            billing_form = UserInfoForm(request.POST, instance=billing_user)
        else:
            # Create a ShippingAddress for Guest Users: We are creating a ShippingForm even if we are not saving the data in DB because we want to validate whatever data the Guest User is putting in as Shipping Info.
            shipping_form = ShippingForm(request.POST)
            billing_form = UserInfoForm(request.POST)

        if shipping_form.is_valid() and billing_form.is_valid():
            # Check for valid form even if user is not logged in, just so they put correct data in.
            if request.user.is_authenticated:
                # Save the form only if user is authenticated
                shipping_form.save()
                billing_form.save()

            return render(request, 'payment/billing_info.html', {'products': products, 'cart_total': cart_total, 'shipping_info': request.POST, 'paypal_form': paypal_form, 'invoice_id': invoice_id})
        
        else:
            for error in list(shipping_form.errors.values()):
                messages.error(request, error)
            return redirect('checkout')
        
        # return render(request, 'payment/billing_info.html', {'products': products, 'cart_total': cart_total, 'shipping_form': shipping_form})
    
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def checkout(request):
    cart = Cart(request)
    products = cart.get_products()
    quantities = cart.get_quantities()

    for product in products:
        product.qty = quantities.get(str(product.id), 1)

        price = product.price
        if product.on_sale:
            price = product.sale_price

        product.total_price = (product.qty) * (price)

    cart_total = cart.cart_total()

    if request.user.is_authenticated:
        # Checkout as LoggedIn User
        shipping_user = ShippingAddress.objects.get(user=request.user)
        billing_user = Profile.objects.get(user=request.user)

        # If User has Email in their User Model then fetch it from there and prepopulate Shipping Form
        if shipping_user.shipping_email == '':
            email = User.objects.get(username=request.user.username).email
            if email == '':
                email = billing_user.email

            shipping_user.shipping_email = email

        billing_form = UserInfoForm(instance=billing_user)
        shipping_form = ShippingForm(instance=shipping_user)
        return render(request, 'payment/checkout.html', {'products': products, 'cart_total': cart_total, 'shipping_form': shipping_form, 'billing_form': billing_form})
    
    else:
        # Checkout as Guest User
        if request.session.get('shipping_info'):
            # If shipping info exists in session then get it from there
            shipping_form = ShippingForm(request.session['shipping_info'])
        else:
            # else create a empty form
            shipping_form = ShippingForm()

        if request.session.get('billing_info'):
            # If shipping info exists in session then get it from there
            billing_form = UserInfoForm(request.session['billing_info'])
        else:
            # else create a empty form
            billing_form = UserInfoForm()

        return render(request, 'payment/checkout.html', {'products': products, 'cart_total': cart_total, 'shipping_form': shipping_form, 'billing_form': billing_form})


def payment_success(request):
    cart = Cart(request)
    # Empty Shopping Cart From Session: Clear the cart dict from our 'cart' object
    cart.clear()

    # Empty Shopping Cart From DB
    if request.user.is_authenticated:
        Profile.objects.filter(user=request.user).update(old_cart="")

    messages.success(request, "Your order has been placed successfully!")
    return render(request, 'payment/payment_success.html', {})


def payment_failed(request, invoice_id):
    # Delete order if payment failed
    Order.objects.filter(invoice_id=invoice_id).delete()
    messages.success(request, "There Was an Error Completing Your Order")
    return render(request, 'payment/payment_failed.html', {})
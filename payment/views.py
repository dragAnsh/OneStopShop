from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from cart.cart import Cart
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
        return render(request, 'payment/user_orders_list.html', {'user_orders': user_orders, 'filter': filter, 'has_orders': has_orders})
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

        # Pagination: Show 5 orders per page
        paginator = Paginator(orders, 5) # Django does not immediately split the queryset. Instead, it: 1. Stores the queryset (orders) internally. 2. Stores the number of objects per page (5). 3. Waits until you request a specific page to slice the queryset dynamically.
        page_number = request.GET.get("page")
        page_orders = paginator.get_page(page_number) # The method converts the page number to an integer. It calculates the start and end indices based on the page size. start = (2 - 1) * 10  # 10 end = start + 10  # 20. It slices the queryset dynamically like this: page_queryset = orders[10:20]  # Equivalent of LIMIT and OFFSET in SQL. It creates a Page object that holds this sliced queryset.

        return render(request, 'payment/shipped_dashboard.html', {'orders': page_orders})
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def not_yet_shipped_dashboard(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False).order_by("-date_ordered")

        # Pagination: Show 5 orders per page
        paginator = Paginator(orders, 5)
        page_number = request.GET.get("page")  # Get the page number from URL
        page_orders = paginator.get_page(page_number) 

        return render(request, 'payment/not_yet_shipped_dashboard.html', {"orders": page_orders})
    else:
        messages.error(request, "ACCESS DENIED!")
        return redirect('home')


def process_order(request):
    if request.method=='POST':
        cart = Cart(request)
        products = cart.get_products()
        quantities = cart.get_quantities()
        cart_total = cart.cart_total()

        # Get Billing Info from last page
        billing_form = PaymentForm(request.POST)

        # Get Shipping Session Data
        shipping_info = request.session.get('shipping_info')

        # Gather Order Info
        # Create Shipping Address Text from Session Info
        include_fields = ("shipping_address1", "shipping_address2", "shipping_city", "shipping_state", "shipping_zipcode", "shipping_country")
        shipping_address = "\n".join(shipping_info[field] for field in include_fields if shipping_info.get(field))

        full_name = shipping_info['shipping_full_name']
        email = shipping_info['shipping_email']
        amount_paid = cart_total
        user = request.user if request.user.is_authenticated else None

        # Create an order
        create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
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
        # Empty Shopping Cart From Session: Clear the cart dict from our 'cart' object
        cart.clear()

        # Empty Shopping Cart From DB
        if request.user.is_authenticated:
            Profile.objects.filter(user=user).update(old_cart="")
            # Send Order Confirmation Email: Use Celery as Distributed Task Queue and Redis as Message Broker 
            send_order_confirmation_email_task.delay(create_order.id)

        messages.success(request, "Order Placed!")
        return redirect('home')
    
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

        # Create a session with Shipping Info
        shipping_info_session = request.POST
        request.session['shipping_info'] = shipping_info_session

        if request.user.is_authenticated:
            # Update the ShippingAddress for LoggedIn Users
            shipping_user = ShippingAddress.objects.get(user=request.user)
            shipping_form = ShippingForm(request.POST, instance=shipping_user)
        else:
            # Create a ShippingAddress for Guest Users: We are creating a ShippingForm even if we are not saving the data in DB because we want to validate whatever data the Guest User is putting in as Shipping Info.
            shipping_form = ShippingForm(request.POST)

        if shipping_form.is_valid():
            # Check for valid form even if user is not logged in, just so they put correct data in.
            if request.user.is_authenticated:
                # Save the form only if user is authenticated
                shipping_form.save()

            # Get the Billing Form
            billing_form = PaymentForm()
            return render(request, 'payment/billing_info.html', {'products': products, 'cart_total': cart_total, 'shipping_info': request.POST, 'billing_form': billing_form})
        
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
        shipping_form = ShippingForm(instance=shipping_user)
        return render(request, 'payment/checkout.html', {'products': products, 'cart_total': cart_total, 'shipping_form': shipping_form})
    else:
        # Checkout as Guest User
        if request.session.get('shipping_info'):
            # If shipping info exists in session then get it from there
            shipping_form = ShippingForm(request.session['shipping_info'])
        else:
            # else create a empty form
            shipping_form = ShippingForm()
        return render(request, 'payment/checkout.html', {'products': products, 'cart_total': cart_total, 'shipping_form': shipping_form})


def payment_success(request):
    return render(request, 'payment/payment_success.html', {})
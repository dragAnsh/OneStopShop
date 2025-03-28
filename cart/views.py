from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from .cart import Cart
from .saved_items import SavedItems
from store.models import Product
from django.http import JsonResponse
# from .models import UserCart


def saved_items(request):
    saved_items = SavedItems(request)
    products = saved_items.get_products()

    return render(request, 'cart/saved_items.html', {'products': products})


def move_all_to_saved_items(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        cart = Cart(request)
        cart.move_all_to_saved_items()
        messages.success(request, "Moved Everything to Saved Items Successfully!")
        return JsonResponse({})


def move_to_saved_items(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        cart = Cart(request)
        product_id = int(request.POST['product_id'])
        cart.move_to_saved_items(product_id)
        messages.success(request, "Saved Product for Later Successfully!")
        return JsonResponse({})
    

def move_all_to_cart(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        saved_items = SavedItems(request)
        saved_items.move_all_to_cart()
        messages.success(request, "Moved Everything to Cart Successfully!")
        return JsonResponse({})


def move_to_cart(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        saved_items = SavedItems(request)
        product_id = int(request.POST['product_id'])
        saved_items.move_to_cart(product_id)
        messages.success(request, "Moved to Cart Successfully!")
        return JsonResponse({})
    

def remove_item(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        saved_items = SavedItems(request)
        product_id = int(request.POST['product_id'])
        saved_items.remove(product_id)
        messages.success(request, "Product Removed Successfully!")
        return JsonResponse({})
    

def save_item(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        saved_items = SavedItems(request)
        product_id = int(request.POST['product_id'])
        saved_items.add(product_id)
        messages.success(request, "Product Added to Saved Items Successfully!")
        return JsonResponse({})


def empty_saved_items(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        saved_items = SavedItems(request)
        saved_items.clear()
        messages.success(request, "Saved Items Emptied Successfully!")
        return JsonResponse({})


def cart_summary(request):
    cart = Cart(request)
    # instead of doing the following, we can also define a fn in our Cart class that gives us all Products that are there in the cart
    # products = Product.objects.filter(id__in=cart.cart.keys())

    products = cart.get_products()
    quantities = cart.get_quantities()

    #  get price
    cart_total = cart.cart_total()

    return render(request, 'cart/cart_summary.html', {'products': products, 'quantities': quantities, 'cart_total': cart_total})
    # return render(request, 'temp.html', {'products': products, 'quantities': quantities}) # trying out a different way


def empty_cart(request):
    if request.method=='POST' and request.POST.get('action')=='post':
        cart = Cart(request)
        cart.clear()
        messages.success(request, "Cart Emptied Successfully!")
        return JsonResponse({})


def cart_add(request):
    # get the cart
    cart = Cart(request)
    # test for POST
    if request.POST.get('action') == 'post':
        # get stuff
        product_id = int(request.POST.get('product_id'))
        product_quantity = int(request.POST.get('product_quantity'))

        # lookup product in DB
        # product = get_object_or_404(Product, id = product_id)

        # save to session
        cart.add(product_id=product_id, quantity=product_quantity)

        # get cart quantity
        cart_quantity = len(cart)

        # return a response
        # response = JsonResponse({'Product Name ': product.name})
        response = JsonResponse({'Cart Quantity': cart_quantity})

        # # Handle adding data to UserCart Model
        # if request.user.is_authenticated:
        #     # if the (user, product) already exists then update it, else create and save it
        #     UserCart.objects.update_or_create(user=request.user, product=product, defaults={'quantity': product_quantity})

        messages.success(request, "Item Added to Cart!")
        return response


def cart_delete(request):
    cart = Cart(request)

    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))

        cart.remove(product_id=product_id)
        # cart_quantity = len(cart)

        response = JsonResponse({})
        # response = JsonResponse({'Cart Quantity': cart_quantity})

        # # Handle deleting data from UserCart Model
        # if request.user.is_authenticated:
        #     UserCart.objects.filter(user=request.user, product__id=product_id).delete()
            
        messages.success(request, "Item Deleted Successfully!")
        return response


def cart_update(request):
    cart = Cart(request)

    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product_quantity = int(request.POST.get('product_quantity'))

        cart.update(product=product_id, quantity=product_quantity)

        response = JsonResponse({'Updated Quantity': product_quantity})

        # # Handle updating data to UserCart Model
        # if request.user.is_authenticated:
        #     # user_cart_item = UserCart.objects.get(user=request.user, product__id=product_id) # get will throw DoesNotExist exception if the item does not exist, so better to use filter instead
        #     updated_rows = UserCart.objects.filter(user=request.user, product__id=product_id).update(quantity=product_quantity)

        #     if updated_rows == 0:
        #         # No matching entry was found, you can handle this case if needed
        #         messages.error(request, "No Matching entires found to Update!")
            
        messages.success(request, "Cart Updated Successfully!")
        return response
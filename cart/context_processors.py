from .cart import Cart


# create a context processor, so our cart is accessible on all pages of the site
def cart(request):
    # return the default Cart object
    return {'cart': Cart(request)}
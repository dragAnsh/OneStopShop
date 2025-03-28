from .saved_items import SavedItems
from .cart import Cart


# create a context processor, so our cart is accessible on all pages of the site
def cart(request):
    # return the default Cart object
    return {'cart': Cart(request)}


def saved_items(request):
    return {'saved_items': SavedItems(request)}
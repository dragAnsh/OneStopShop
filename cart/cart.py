from .saved_items import SavedItems
from  store.models import Product, Profile
import json


class Cart:
    def __init__(self, request):
        self.session = request.session # self.session is an alias of request.session
        self.request = request # Get the request so that we can use it across this class Cart

        # get the current cart items if they exist (we are using session key as the variable name here)
        cart = self.session.get('session_key') # cart is a local variable inside __init__

        # if the user is new or have nothing in cart then we don't see any session key. thus cart(local var) will be none
        if 'session_key' not in self.session:
            cart = self.session['session_key'] = {}


        # make sure this shopping cart work on every page of website i.e. all templates. Also we need context processor
        self.cart = cart
        
        # or do this instead
        # self.cart = self.session.get('session_key', {})
        # self.session['session_key'] = self.cart

        # Cache Products in the Cart to avoid duplicate queries
        self._products_cache = None

    
    def update_db(self):
        # updates the user's cart in db if he is logged in
        if self.request.user.is_authenticated:
            # Get the current user profile
            current_user_profile = Profile.objects.filter(user=self.request.user)
            # convert our self.cart to a JSON string to store in the DB
            new_cart_str = json.dumps(self.cart)
            current_user_profile.update(old_cart=new_cart_str)


    def db_add(self, saved_cart_dict):
        for product_id, quantity in saved_cart_dict.items():
            # if the product id doesn't exist then we create a new field
            if product_id not in self.cart:
                self.cart[product_id] = quantity
            # else we just let the session quantity be the final quantity and not update it by quantity from DB
            else:
                pass
        
        self.session.modified = True

        # Deal With Logged In Users: If we log out and then add some stuff while being logged out and then log back in so we wanna update our DB to have those items as well
        self.update_db()
        self._products_cache = None # Reset cache


    def add(self, product_id, quantity):
        product_id = str(product_id) # converting it to string because we are going to use it as a key in our cart dictionary

        # logic
        # if product_id not in self.cart:
        #     self.cart[product_id] = {'price': str(product.price)}
        # else:
        #     pass

        if product_id not in self.cart:
            self.cart[product_id] = quantity
        else:
            # if the user adds a product and some qty to cart that (product) already exists then increase the quantity by that qty
            # self.cart[product_id] = self.cart[product_id] + quantity

            # or just update the quantity
            self.cart[product_id] = quantity

        # tell django that we have made some changes to session and django needs to save it. Ow Django might miss small changes and do lazy saving later on.
        self.session.modified = True

        # Deal With Logged In Users
        self.update_db()
        self._products_cache = None # Reset cache


    def __len__(self):
        # now you can use len() function on a Cart object or use 'length' filter on Cart object
        return len(self.cart)
    
    
    def get_products(self):
        if self._products_cache is None:
            # get ids from cart
            product_ids = self.cart.keys()

            # use ids to lookup products in DB
            self._products_cache = Product.objects.filter(id__in=product_ids)
    
            # me trying to return a list of 2-tuple (product and it's quantity)
            # temp = []

            # for product in products:
            #     temp.append((product, self.cart[str(product.id)]))

            # return temp
        return self._products_cache


    def get_quantities(self):
        return self.cart
   
    
    def update(self, product, quantity):
        product_id = str(product)
        self.cart[product_id] = quantity

        self.session.modified = True

        # Deal with logged in users
        self.update_db()
        self._products_cache = None # Reset cache

    
    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.session.modified = True  # Save changes

        # Deal with logged in users
        self.update_db()
        self._products_cache = None # Reset cache

    
    def cart_total(self):
        products = self.get_products()
        total_price = 0.0

        for product in products:
            # total price of a product: qty * unit price
            qty = self.cart[str(product.id)]

            product_price = product.price

            if product.on_sale:
                product_price = product.sale_price

            price = float(product_price) * qty
            total_price += price        

        return round(total_price, 2)
    

    def clear(self):
        self.cart.clear()
        self.update_db()
        self.session.modified = True  # Ensure session updates
        # or
        # del self.session['session_key']
        self._products_cache = None # Reset cache

    
    def move_to_saved_items(self, product_id):
        saved_items = SavedItems(self.request)
        saved_items.add(product_id)
        self.remove(product_id)

    
    def move_all_to_saved_items(self):
        product_ids = list(self.cart.keys())
        for product_id in product_ids:
            self.move_to_saved_items(product_id)
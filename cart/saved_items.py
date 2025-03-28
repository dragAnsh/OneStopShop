from store.models import Profile, Product

class SavedItems:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.saved_items = self.session.get('saved_items', []) # List of Product ID's. We don't need quantities.
        self.session['saved_items'] = self.saved_items


    def update_db(self):
        if self.request.user.is_authenticated:
            saved_items_str = str(self.saved_items)
            Profile.objects.filter(user=self.request.user).update(saved_items=saved_items_str)


    def add(self, product_id):
        product_id = int(product_id)
        if product_id not in self.saved_items:
            self.saved_items.append(product_id)
            self.session.modified = True
            self.update_db()


    def db_add(self, saved_items_list):
        for product_id in saved_items_list:
            self.add(product_id)
        self.update_db()


    def remove(self, product_id):
        self.saved_items.remove(product_id)
        self.session.modified = True
        self.update_db()


    def get_products(self):
        return Product.objects.filter(id__in=self.saved_items)
    

    def move_to_cart(self, product_id):
        from .cart import Cart
        cart = Cart(self.request)
        cart.add(product_id=product_id, quantity=1)
        self.remove(product_id)

    
    def move_all_to_cart(self):
        product_ids = self.saved_items[:]
        for product_id in product_ids:
            self.move_to_cart(product_id)

    
    def clear(self):
        self.saved_items.clear()
        self.update_db()
        self.session.modified = True
    

    def __len__(self):
        return len(self.saved_items)
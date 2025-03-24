from django.db import models
from store.models import Product
from django.contrib.auth.models import User


# For now not using this and instead using: converting dict to string and saving it to DB and then unpacking it at time of login
class UserCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.user.first_name}'s Cart"
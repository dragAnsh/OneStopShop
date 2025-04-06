from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.timezone import now
from cloudinary.models import CloudinaryField


# Create Customer Profile: Extend User Model and Associate it with Django User Authentication Model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Link User Model to Profile by a OneToOne Relationship
    # date_created = models.DateTimeField(default=datetime.datetime.today()) # updates only once when the object is created, does not account for timezone instead uses system time
    # date_created = models.DateTimeField(default=now) # updates only once when the object is created, accounts for timezone too, another way to do auto_now_add but you can change this field
    date_created = models.DateTimeField(auto_now_add=True) # updates only once when the object is created, accounts for timezone too, can not be changed ever
    date_modified = models.DateTimeField(auto_now=True) # is udpated every time the object is saved
    phone = models.CharField(max_length=10, blank=True)
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zipcode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=50, blank=True)
    old_cart = models.CharField(max_length=200, blank=True, null=True)
    saved_items = models.CharField(max_length=200, default="[]", blank=True, null=True)

    def __str__(self):
        return self.user.username


# create a user profile by default when user signs up: User signs up, User object is saved, Post Save Signal is sent, Django calls create_profile method and passes sender = User Model, instance = Current Logged in User, created = True if the user is created for first time and not being updated.
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save() # save the Profile Object that was just created for the current user


# Automate the profile thing: create a profile for user automatically when they sign up
# The .connect() method tells Django to run a function (create_profile) when an event (post_save) happens on a specific model (sender=User).
post_save.connect(create_profile, sender=User) # sender is the model that is trigerring this function


# Categories of Products
class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=6)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(max_length=200, default='', blank=True, null=True)
    # image = models.ImageField(upload_to='uploads/product/') # media/uploads/product
    image = CloudinaryField('image')
    on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=6)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_people_rated = models.PositiveIntegerField(default=0)
    total_ratings_sum = models.PositiveIntegerField(default=0)

    def update_rating(self, user_rating):
        self.total_ratings_sum += int(user_rating)
        self.total_people_rated += 1
        self.average_rating = round(self.total_ratings_sum / self.total_people_rated, 2)
        self.save()

    def __str__(self):
        return self.name
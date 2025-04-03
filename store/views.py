from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, UpdateUserForm, UpdatePasswordForm, UserInfoForm
from payment.forms import ShippingForm
from django.db.models import Q
from cart.cart import Cart
from cart.saved_items import SavedItems
from payment.models import ShippingAddress
# from cart.models import UserCart
import json
from django.db.models import Exists, OuterRef
from payment.tasks import send_user_registration_email_task


def search(request):
    # Determine if they filled out the form
    if request.method=='POST':
        search_text = request.POST['search_text']

        # Query the Product DB
        # Q makes Django queries flexible and powerful. Internally, it constructs SQL WHERE clauses dynamically.
        search_result = Product.objects.filter(Q(name__icontains=search_text) | Q(description__icontains=search_text)) # Normally, Django queries are AND-based by default. With Q, we can use | (OR), & (AND), and ~ (NOT).
        # Test for Null
        if not search_result:
            messages.success(request, "Requested Product Does Not Exist. Please Try Again Later!")
            return render(request, 'store/search.html', {})

        return render(request, 'store/search.html', {'search_result': search_result})
    else:
        return render(request, 'store/search.html', {})


def update_info(request):
    if request.user.is_authenticated:
        # current_user = Profile.objects.get(user__id=request.user.id)
        current_user = Profile.objects.get(user=request.user)
        # Get current User's Shipping info: if the user's shipping address model doesn't exist then it will create it
        shipping_user, created = ShippingAddress.objects.get_or_create(user=request.user)

        if request.method=='POST':
            form = UserInfoForm(request.POST, instance=current_user)
            shipping_form = ShippingForm(request.POST, instance=shipping_user)

            if form.is_valid() and shipping_form.is_valid():
                form.save()
                shipping_form.save()
                messages.success(request, "Your Info Has Been Updated Successfully!")
                return redirect('home')

            elif form.is_valid():
                form.save()
                messages.success(request, "Your Profile Info Has Been Updated, But There are some errors in Your Shipping Info!")

                for error in list(shipping_form.errors.values()):
                    messages.error(request, error)

                return redirect('update_info')

            elif shipping_form.is_valid():
                shipping_form.save()
                messages.success(request, "Your Shipping Info Has Been Updated, But There are some errors in Your Profile Info!")

                for error in list(form.errors.values()):
                    messages.error(request, error)

                return redirect('update_info')

            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                for error in list(shipping_form.errors.values()):
                    messages.error(request, error)
                return redirect('update_info')
            
        else: # Handling GET requests
            form = UserInfoForm(instance=current_user)
            shipping_form = ShippingForm(instance=shipping_user)
            return render(request, 'store/update_info.html', {'form': form, 'shipping_form': shipping_form})
    
    else:
        messages.success(request, "You Must Be Logged In To Access the Page!")
        return redirect('home')


def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user

        if request.method=='POST': # Handling POST requests: Did they fill out the form
            form = UpdatePasswordForm(current_user, request.POST) # For SetPasswordForm current_user must be the first positional argument and it doesnt have any 'instance' keyword arg
            if form.is_valid():
                form.save()
                login(request, current_user) # After Updating user we have to log them back in. When you call .set_password() (which SetPasswordForm.save() does internally), Django: Changes the password. Invalidates all active sessions for security reasons.
                messages.success(request, "Your Password Has Been Updated Successfully!")
                return redirect('update_user')
            
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                return redirect('update_password')

        else: # Handling GET requests
            form = UpdatePasswordForm(current_user) # current_user is necessary because SetPasswordForm needs it to update the password for the correct user.
            return render(request, 'store/update_password.html', {'form': form})
    
    else:
        messages.success(request, "You Must Be Logged In To Access the Page!")
        return redirect('home')


def update_user(request):
    if request.user.is_authenticated:
        # current_user = User.objects.get(id=request.user.id) # Get Current logged in user
        current_user = request.user # Same way to achieve the same thing whilst saving 1 DB query

        if request.method=='POST': # Handling POST requests
            user_form = UpdateUserForm(request.POST, instance=current_user) # instance allows the current user's info being pre filled.
            if user_form.is_valid():
                user_form.save()
                login(request, current_user) # After Updating user we have to log them back in
                messages.success(request, "Your Profile Info Has Been Updated Successfully!")
                return redirect('home')
            
            else:
                for error in list(user_form.errors.values()):
                    messages.error(request, error)
                return redirect('update_user')

        else: # Handling GET requests
            user_form = UpdateUserForm(instance=current_user)
            return render(request, 'store/update_user.html', {'user_form': user_form})
    
    else:
        messages.success(request, "You Must Be Logged In To Access the Page!")
        return redirect('home')


    # return render(request, 'store/update_user.html', {})


def category_summary(request):
    # add 'has_products' field to each entry in the queryset. Thus only pass categories that has atleast one product in them
    categories = Category.objects.annotate(has_products=Exists(Product.objects.filter(category=OuterRef('pk')))).filter(has_products=True)
    return render(request, 'store/category_summary.html', {'categories': categories})


def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})


def about(request):
    return render(request, 'store/about.html', {})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Hadle Merging Cart From DB to session
            current_user_profile = Profile.objects.get(user=request.user)

            # Get their saved cart from DB and convert DB string to Python Dict if there are items in cart
            saved_cart_str = current_user_profile.old_cart

            if saved_cart_str:
                saved_cart_dict = json.loads(saved_cart_str)

                # Add the loaded cart dict to our session
                cart = Cart(request)
                cart.db_add(saved_cart_dict)

            # Handle Merging SavedItems from DB to session
            saved_items_str = current_user_profile.saved_items
            saved_items_list = json.loads(saved_items_str)

            saved_items = SavedItems(request)
            saved_items.db_add(saved_items_list)

            messages.success(request, "You have Successfully Logged In!")
            return redirect('home')
        
        else:
            messages.success(request, "There was an error Logging You In!")
            return redirect('login')
    else:
        return render(request, 'store/login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, "You have been Successfully Logged Out!")
    return redirect('home')


def register_user(request):
    form = SignUpForm()

    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            user = authenticate(username=username, password=password)
            login(request, user)

            # Send Registration Email to User
            user_email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            send_user_registration_email_task.delay(user_email, first_name)

            messages.success(request, "Username Created- Please Fill Out The Info Below")
            return redirect('update_info')
        
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
            return render(request, 'store/register.html', {'form': form})

    else:
        return render(request, 'store/register.html', {'form': form})


def product(request, pk):
    product = Product.objects.get(id=pk)
    return render(request, 'store/product.html', {'product': product})


def category(request, cat):
    # replace hyphens with spaces
    cat = cat.replace('-', ' ')

    # try:
    #     # find the category object and then do a filter on that object
    #     category = Category.objects.get(name=cat) # this will throw a DoesNotExist Exception so the except block will catch it. But when seraching directly using the __ lookup, the try except won't help because it will return empty queryset. so having a exists() check will be good instead of try except.
    #     products = Product.objects.filter(category=category)

    #     return render(request, 'store/category.html', {'products': products, 'category': cat})
    # except:
    #     messages.success(request, "The requested Category Doesn't Exist!")
    #     return redirect('home')

    

    # or just do a __lookup to filter out based on name directly
    products = Product.objects.filter(category__name=cat) # returns an empty queryset in case category doesn't exist
    if products.exists():
        return render(request, 'store/category.html', {'products': products, 'category': cat})
    else:
        messages.success(request, "The requested Category Is Either Empty Or Doesn't Exist!")
        return redirect('home')
from django.shortcuts import render, redirect
from store.documents import ProductDocument
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, UpdateUserForm, UpdatePasswordForm, UserInfoForm
from payment.forms import ShippingForm
from cart.cart import Cart
from cart.saved_items import SavedItems
from payment.models import ShippingAddress
# from cart.models import UserCart
import json
from django.db.models import Exists, OuterRef
from payment.tasks import send_user_registration_email_task
from .utils import get_rating_stats, search_with_pagination
from django.http import JsonResponse


def autocomplete_suggestions(request):
    # get the search_text from the request
    search_text = request.GET.get('search_text', '').strip()

    if not search_text:
        return JsonResponse({'suggestions': []})
    
    search_query = ProductDocument.search().suggest(
        "product-suggest", # named suggester
        search_text,
        completion={
            "field": "name_suggest",
            "size": 5
        }
    ).suggest(
        "category-suggest", # named suggester
        search_text,
        completion={
            "field": "category_suggest",
            "size": 5
        }
    )

    # Execute the suggest query
    response = search_query.execute()

    # Extract results
    suggestions = []

    for option in response.suggest['product-suggest'][0].options:
        suggestions.append(option._source.name)
    
    for option in response.suggest['category-suggest'][0].options:
        suggestions.append(option._source.name)

    return JsonResponse({"suggestions": suggestions})


def search(request):
    # Use GET for search so that you have a sharable URL
    if request.method=='GET':
        search_text = request.GET.get('search_text', '').strip()
        price_filter = request.GET.get('price_filter', '')
        sale_filter = request.GET.get('sale_filter', '')
        rating_filter = request.GET.get('rating_filter', '1_and_up')
        page = max(int(request.GET.get('page', 1)), 1) # make sure page is >= 1

        if not search_text:
            return redirect('home')
        
        data = search_with_pagination(search_text, price_filter, sale_filter, rating_filter, page)
        search_result = data['result']

        return render(request, 'store/search.html', {'search_result': search_result, 'search_text': search_text, 'price_filter': price_filter, 'sale_filter': sale_filter, 'rating_filter': rating_filter, 'total_pages': data['total_pages'], 'current_page': data['current_page']})
    
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

                for field, errors in shipping_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field[9:].replace('_', ' ').title()} in Shipping Information: {error}")

                return redirect('update_info')

            elif shipping_form.is_valid():
                shipping_form.save()
                messages.success(request, "Your Shipping Info Has Been Updated, But There are some errors in Your Profile Info!")

                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').title()} in Billing Information: {error}")

                return redirect('update_info')

            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').title()} in Billing Information: {error}")

                for field, errors in shipping_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field[9:].replace('_', ' ').title()} in Shipping Information: {error}")

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
    rating_percentages = get_rating_stats(product)['rating_percentages']
    return render(request, 'store/product.html', {'product': product, 'rating_percentages': rating_percentages})


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
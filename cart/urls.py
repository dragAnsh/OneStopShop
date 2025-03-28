from django.urls import path
from . import views


urlpatterns = [
    path('', views.cart_summary, name='cart_summary'),
    path('add/', views.cart_add, name='cart_add'),
    path('delete/', views.cart_delete, name='cart_delete'),
    path('update/', views.cart_update, name='cart_update'),
    path('empty_cart/', views.empty_cart, name='empty_cart'),
    path('move_to_saved_items/', views.move_to_saved_items, name='move_to_saved_items'),
    path('move_all_to_saved_items/', views.move_all_to_saved_items, name='move_all_to_saved_items'),
    path('move_to_cart/', views.move_to_cart, name='move_to_cart'),
    path('move_all_to_cart/', views.move_all_to_cart, name='move_all_to_cart'),
    path('save_item/', views.save_item, name='save_item'),
    path('remove_item/', views.remove_item, name='remove_item'),
    path('empty_saved_items/', views.empty_saved_items, name='empty_saved_items'),
    path('saved_items/', views.saved_items, name='saved_items'),
]
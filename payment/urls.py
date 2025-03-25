from django.urls import path
from . import views


urlpatterns = [
    path('payment_success/', views.payment_success, name = 'payment_success'),
    path('checkout/', views.checkout, name = 'checkout'),
    path('billing_info/', views.billing_info, name = 'billing_info'),
    path('process_order/', views.process_order, name = 'process_order'),
    path('shipped_dashboard/', views.shipped_dashboard, name = 'shipped_dashboard'),
    path('not_yet_shipped_dashboard/', views.not_yet_shipped_dashboard, name = 'not_yet_shipped_dashboard'),
    path('orders/<int:pk>/', views.orders, name = 'orders'),
    path('order_item/<int:pk>/', views.order_item, name = 'order_item'),
    path('mark_shipped/<int:order_id>/', views.mark_shipped, name = 'mark_shipped'),
    path('mark_unshipped/<int:order_id>/', views.mark_unshipped, name = 'mark_unshipped'),
    path('user_orders/<int:order_id>/', views.user_order_detail, name = 'user_order_detail'),
    path('user_orders/<str:filter>/', views.user_orders_list, name = 'user_orders_list'),
    path('user_order_item/<int:pk>/', views.user_order_item, name = 'user_order_item'),
    path('repeat_order/<int:order_id>/', views.repeat_order, name = 'repeat_order'),
    path('generate_invoice/<int:order_id>/', views.generate_invoice, name = 'generate_invoice'),
]
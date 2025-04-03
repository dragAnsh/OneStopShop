from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment'

    # Connect the signals when your project initializes: import the module that register PayPal Signal Handler (Set up PayPal IPN signal)
    def ready(self):
        import payment.hooks

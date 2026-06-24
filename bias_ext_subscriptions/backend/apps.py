from django.apps import AppConfig

class SubscriptionsExtensionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bias_ext_subscriptions.backend"
    label = "subscriptions"

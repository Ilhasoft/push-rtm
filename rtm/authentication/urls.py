from django.conf.urls import url

from .views import LoginAuthView, CallbackAuthView

urlpatterns = [
    url(r"^$", LoginAuthView.as_view(), {}, "authentication.login"),
    url(r"^callback/$", CallbackAuthView.as_view(), {}, "authentication.callback"),
]

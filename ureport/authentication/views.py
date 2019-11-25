from django.conf import settings
from smartmin.views import SmartTemplateView
from requests_oauthlib import OAuth2Session


class LoginAuthView(SmartTemplateView):
    template_name = "authentication/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        org = self.request.org
        context["org"] = org

        oauth = OAuth2Session(
            settings.OAUTHLIB_CLIENT_ID,
            redirect_uri=settings.OAUTHLIB_REDIRECT_URI,
            scope="openid email profile",
            state=org.subdomain if hasattr(org, "subdomain") else None,
        )
        authorization_url, state = oauth.authorization_url(settings.OAUTHLIB_AUTHORIZATION_URL)

        context["authorization_url"] = authorization_url
        context["state"] = state

        print(context)

        return context

import base64
import json
import random

import requests
from requests_oauthlib import OAuth2Session
from smartmin.views import SmartTemplateView

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import Group
from django.shortcuts import redirect, reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _


class LoginAuthView(SmartTemplateView):
    template_name = "authentication/login.html"

    def get(self, request, *args, **kwargs):
        try:
            code = self.request.GET.get("code")
            org = self.request.org

            context = self.get_context_data(**kwargs)
            context["org"] = org

            oauth = OAuth2Session(
                settings.OAUTHLIB_CLIENT_ID,
                redirect_uri=settings.OAUTHLIB_REDIRECT_URI,
                scope="openid email profile",
                state=str(base64.b64encode(org.subdomain.encode("utf-8")), "utf-8") if hasattr(org, "subdomain") else None,
            )

            if code:
                fetch_token = oauth.fetch_token(
                    settings.OAUTHLIB_TOKEN_URL,
                    code=code,
                    include_client_id=settings.OAUTHLIB_CLIENT_ID,
                    client_secret=settings.OAUTHLIB_SECRET,
                    auth="",
                )

                token = fetch_token.get("access_token")
                session = OAuth2Session(client_id=settings.OAUTHLIB_CLIENT_ID, token=token)
                session.access_token = token
                user_data = session.get(url=settings.OAUTHLIB_USER_URL).json()

                response = requests.post(
                    settings.OAUTHLIB_MOMSERVICE_TOKEN_URL,
                    data={"app_secret": settings.OAUTHLIB_SECRET, "app_id": settings.OAUTHLIB_APP_ID},
                )

                response = requests.post(
                    settings.OAUTHLIB_MOMSERVICE_USER_URL,
                    data={"username": user_data.get("preferred_username")},
                    headers={"authorizationtoken": response.json().get("data").get("token")},
                )

                extra_data = json.loads(response.text).get("data")
                workspace = extra_data.get("workspace")

                if self.request.org.subdomain in workspace:
                    try:
                        user = get_user_model().objects.get(
                            email=extra_data.get("email"), username=extra_data.get("userid")
                        )
                    except get_user_model().DoesNotExist:
                        user = get_user_model().objects.create(
                            username=extra_data.get("userid"),
                            first_name=extra_data.get("username"),
                            email=extra_data.get("email"),
                        )
                        user.set_password(random.getrandbits(128))
                        user.save()

                        group = Group.objects.get(name="Viewers")
                        user.groups.add(group)
                        self.request.org.viewers.add(user)

                    login(self.request, user)
                    return redirect(reverse("dashboard"))
            else:
                authorization_url, state = oauth.authorization_url(settings.OAUTHLIB_AUTHORIZATION_URL)
                context["authorization_url"] = authorization_url
        except Exception:
            messages.error(self.request, _("Please try again."))
            return redirect(reverse("authentication.login"))

        return self.render_to_response(context)


class CallbackAuthView(SmartTemplateView):
    template_name = "authentication/login.html"

    def get(self, request, *args, **kwargs):
        state = self.request.GET.get("state")
        code = self.request.GET.get("code")

        if state and code:
            state = str(base64.b64decode(state.encode("UTF-8")), "utf-8")
            return redirect("{}/authentication/?code={}".format(settings.SITE_HOST_PATTERN.format(state), code))
        return super().get(request)

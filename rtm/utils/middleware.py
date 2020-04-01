from django.http import HttpResponseRedirect
from dash.orgs.middleware import SetOrgMiddleware

from django.conf import settings


class CheckVersionMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):

        new_design = False
        org = request.org
        if org:
            new_design = org.get_config("common.has_new_design", False)

        path = request.get_full_path_info()
        if (
            new_design
            and not path.startswith("/v2/")
            and not path.startswith("/v1/")
            and not path.startswith("/media/")
            and not path.startswith("/api/")
            and not path.startswith("/count")
            and not path.startswith("/status")
            and not path.startswith("/sitestatic")
        ):
            return HttpResponseRedirect(f"/v2{path}")

        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if request.path.startswith("/v2/"):
            current_t_names = response.template_name
            response.template_name = [f"v2/{elt}" if not elt.startswith("v2/") else elt for elt in current_t_names]
        return response


class SetOrgRequestMiddleware(SetOrgMiddleware):
    def get_subdomain(self, request):
        subdomain = ""
        parts = self.get_host_parts(request)
        host_string = ".".join(parts)

        # we only look up subdomains for localhost and the configured hostname only
        top_domains = ["localhost:8000", "localhost", getattr(settings, "HOSTNAME", "")]
        allowed_top_domain = False
        for top in top_domains:
            if host_string.endswith(top):
                allowed_top_domain = True
                break

        # if empty parts or domain neither localhost nor hostname return ""
        if not parts or not allowed_top_domain:
            return "lso"

        # if we have parts for domain like 'www.nigeria.ureport.in'
        if len(parts) > 2:
            subdomain = parts[0]
            parts = parts[1:]

            # we keep stripping subdomains if the subdomain is something
            # like 'www' and there are more parts
            while subdomain.lower() == "www" and len(parts) > 1:
                subdomain = parts[0]
                parts = parts[1:]

        elif len(parts) > 0:
            # for domains like 'ureport.in' we just take the first part
            subdomain = parts[0]

        # get the configured hostname
        hostname = getattr(settings, "HOSTNAME", "")
        domain_first_part = hostname.lower().split(".")[0]

        # if the subdomain is the same as the first part of hostname
        # ignore than and return ''
        if subdomain.lower() in [domain_first_part, "localhost"]:
            subdomain = ""

        return subdomain

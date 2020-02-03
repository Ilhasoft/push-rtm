from dash.orgs.models import Org
from ureport.celery import app

from .models import OrgCountryCode


@app.task()
def create_org_country_code(*args, **kwargs):
    org_id = kwargs.get("org_id")
    if org_id:
        org = Org.objects.get(pk=org_id)
        temba_cliente = org.get_temba_client()
        if temba_cliente:
            data_org = temba_cliente.get_org()
            if data_org:
                code = data_org.country
                if code:
                    exist = OrgCountryCode.objects.filter(org_country_code=code).exists()

                    if not exist:
                        org_country_code = OrgCountryCode.objects.create(org_country_code=code, org=org)

                    if not org_country_code:
                        raise Exception

    return True

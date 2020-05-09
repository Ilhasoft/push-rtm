from dash.orgs.models import Org
from temba_client.v2 import TembaClient

from rtm.celery import app

from .models import OrgCountryCode


@app.task()
def create_org_country_code(*args, **kwargs) -> bool:
    try:
        org_id: int = kwargs.get("org_id")
        org: Org = Org.objects.get(pk=org_id)

        already_exist: bool = OrgCountryCode.objects.filter(org=org).exists()
        if already_exist:
            return True

        temba_cliente: TembaClient = org.get_temba_client()
        temba_org: Org = temba_cliente.get_org()
        code: str = temba_org.country
        OrgCountryCode.objects.create(org_country_code=code, org=org)

    except Exception as e:
        pass

    return True

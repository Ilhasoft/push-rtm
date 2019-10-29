from django.conf import settings


def sdg_list(request):
    return {"SDG_LIST": settings.SDG_LIST}

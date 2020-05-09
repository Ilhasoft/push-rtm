# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from django.conf.urls import url

from .views import PollCRUDL, FlowDataView

urlpatterns = PollCRUDL().as_urlpatterns()
urlpatterns += [
    url(
        r"^data/(?P<global_survey>[0-9]+)/(?P<flow_uuid>[\w\-]+)/$",
        FlowDataView.as_view(),
        name="polls.flow_data_view",
    ),
]

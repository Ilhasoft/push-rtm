# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import url

from .views import PollCRUDL

urlpatterns = PollCRUDL().as_urlpatterns()

# urlpatterns = [
#     url(r"^$", PollCRUDL.List.as_view(), name="surveys.poll_list"),
#     url(r"^create/$", PollCRUDL.Create.as_view(), name="surveys.poll_create"),
#     url(r"^update/(?P<pk>\d+)/$", PollCRUDL.Update.as_view(), name="surveys.poll_update"),
#     url(r"^date/(?P<pk>\d+)/$", PollCRUDL.PollDate.as_view(), name="surveys.poll_date"),
#     url(r"^questions/(?P<pk>\d+)/$", PollCRUDL.Questions.as_view(), name="surveys.poll_questions"),
# ]

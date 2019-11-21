# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json

from dash.orgs.models import Org
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from ureport.api.serializers import (
    OrgReadSerializer,
    PollReadSerializer,
)
from ureport.polls.models import Poll
from ureport.dashboard.views import DashboardDataView


class OrgList(ListAPIView):
    """
    This endpoint allows you to list orgs.

    ## Listing Orgs

    By making a ```GET``` request you can list all the organisations.  Each org has the following attributes:

    * **id** - the ID of the org (int)
    * **logo_url** - the LOGO_URL of the org (string)
    * **name** - the NAME of the org (string)
    * **language** - the LANGUAGE of the org (string)
    * **subdomain** - the SUBDOMAIN of of this org (string)
    * **domain** - the DOMAIN of of this org (string)
    * **timezone** - the TIMEZONE of of this org (string)

    Example:

        GET /api/v1/orgs/

    Response is the list of orgs:

        {
            "count": 389,
            "next": "/api/v1/polls/orgs/?page=2",
            "previous": null,
            "results": [
            {
                "id": 1,
                "logo_url": "http://test.ureport.in/media/logos/StraightOuttaSomewhere_2.jpg",
                "name": "test",
                "language": "en",
                "subdomain": "test",
                "domain": "ureport.in",
                "timezone": "Africa/Kampala"
                "gender_stats": {
                    "female_count": 0,
                    "male_percentage": "---",
                    "female_percentage": "---",
                    "male_count": 0
                },
                "age_stats": [],
                "registration_stats": [{"count": 0, "label": "07/06/15"}],
                "occupation_stats": []
            },
            ...
        }
    """

    serializer_class = OrgReadSerializer
    queryset = Org.objects.filter(is_active=True)


class OrgDetails(RetrieveAPIView):
    """
    This endpoint allows you to get a single org.

    ## Get a single org

    Example:

        GET /api/v1/orgs/1/

    Response is a single org with that ID:

        {
            "id": 1,
            "logo_url": "http://test.ureport.in/media/logos/StraightOuttaSomewhere_2.jpg",
            "name": "test",
            "language": "en",
            "subdomain": "test",
            "domain": "ureport.in",
            "timezone": "Africa/Kampala"
            "gender_stats": {
                    "female_count": 0,
                    "male_percentage": "---",
                    "female_percentage": "---",
                    "male_count": 0
                },
            "age_stats": [],
            "registration_stats": [{"count": 0, "label": "07/06/15"}],
            "occupation_stats": []
        }
    """

    serializer_class = OrgReadSerializer
    queryset = Org.objects.filter(is_active=True)


class BaseListAPIView(ListAPIView):
    def get_queryset(self):
        q = self.model.objects.filter(is_active=True).order_by("-created_on")
        if self.kwargs.get("org", None):
            q = q.filter(org_id=self.kwargs.get("org"))
        return q


class PollList(BaseListAPIView):
    """
    This endpoint allows you to list polls.

    ## Listing Polls

    By making a ```GET``` request you can list all the polls for an organization, filtering them as needed.  Each
    poll has the following attributes:

    * **id** - the ID of the poll (int)
    * **flow_uuid** - the FLOW_UUID of the run (string) (filterable: ```flow_uuid```)
    * **title** - the TITLE of the poll (string)
    * **org** - the ID of the org that owns this poll (int)
    * **category** - the CATEGORIES of of this poll (dictionary)

    Example:

        GET /api/v1/polls/org/1/

    Response is the list of polls, most recent first:

        {
            "count": 389,
            "next": "/api/v1/polls/org/1/?page=2",
            "previous": null,
            "results": [
                {
                    "id": 2,
                    "flow_uuid": "a497ba0f-6b58-4bed-ba52-05c3f40403e2",
                    "title": "Food Poll",
                    "org": 1,
                    "category": {
                        "image_url": null,
                        "name": "Education"
                     },
                    "questions": [
                        {
                            "id": 14,
                            "title": "Are you hungry?",
                            "ruleset_uuid": "ea74b2c2-7425-443a-97cb-331d4e11abb6",
                            "results":
                                 {
                                     "open_ended": false,
                                     "set": 100,
                                     "unset": 150,
                                     "categories": [
                                         {
                                             "count": 60,
                                             "label": "Yes"
                                         },
                                         {
                                              "count": 30,
                                              "label": "NO"
                                         },
                                         {
                                              "count": 10,
                                              "label": "Thirsty"
                                         },
                                         {
                                              "count": 0,
                                              "label": "Other"
                                         },
                                     ]
                                 }
                        },
                        {



                            "id": 16,
                            "title": "What would you like to eat",
                            "ruleset_uuid": "66e08f93-cdff-4dbc-bd02-c746770a4fac",
                            "results":
                                {
                                    "open_ended": true,
                                    "set": 70,
                                    "unset": 30,
                                    "categories": [
                                        {
                                            "count": 40,
                                            "label": "Food"
                                        },
                                        {
                                            "count": 10,
                                            "label": "Cake"
                                        },
                                        {
                                            "count": 15,
                                            "label": "Fruits"
                                        },
                                        {
                                            "count": 5,
                                            "label": "Coffee"
                                        },
                                    ]
                                }
                        },
                        {
                            "id": 17,
                            "title": "Where would you like to eat?",
                            "ruleset_uuid": "e31755dd-c61a-460c-acaf-0eeee1ce0107",
                            "results":
                                {
                                    "open_ended": false,
                                    "set": 50,
                                    "unset": 20,
                                    "categories": [
                                        {
                                            "count": 30,
                                            "label": "Home"
                                        },
                                        {
                                            "count": 12,
                                            "label": "Resto"
                                        },
                                        {
                                            "count": 5,
                                            "label": "Fast Food"
                                        },
                                        {
                                            "count": 3,
                                            "label": "Other"
                                        },
                                    ]
                                }
                        }

                    ]


                    "category": {
                        "image_url": "http://test.ureport.in/media/categories/StraightOuttaSomewhere_2.jpg",
                        "name": "tests"
                    },
                    "created_on": "2015-09-02T08:53:30.313251Z"
                }
                ...
            ]
        }
    """

    serializer_class = PollReadSerializer
    model = Poll

    def get_queryset(self):
        q = super(PollList, self).get_queryset()
        if self.request.query_params.get("flow_uuid", None):
            q = q.filter(flow_uuid=self.request.query_params.get("flow_uuid"))
        return q


class PollDetails(RetrieveAPIView):
    """
    This endpoint allows you to get a single poll.

    ## Get a single poll

    Example:

        GET /api/v1/polls/1/

    Response is a single poll with that ID:

        {
            "id": 2,
            "flow_uuid": "a497ba0f-6b58-4bed-ba52-05c3f40403e2",
            "title": "Food Poll",
            "org": 1,
            "category": {
                "image_url": null,
                "name": "Education"
            },
            "questions": [
                {
                    "id": 14,
                    "title": "Are you hungry?",
                    "ruleset_uuid": "ea74b2c2-7425-443a-97cb-331d4e11abb6",
                    "results":
                        {
                            "open_ended": false,
                            "set": 100,
                            "unset": 150,
                            "categories": [
                                {
                                    "count": 60,
                                    "label": "Yes"
                                },
                                {
                                    "count": 30,
                                    "label": "NO"
                                },
                                {
                                    "count": 10,
                                    "label": "Thirsty"
                                },
                                {
                                    "count": 0,
                                    "label": "Other"
                                },
                            ]
                        }
                },
                {
                    "id": 16,
                    "title": "What would you like to eat",
                    "ruleset_uuid": "66e08f93-cdff-4dbc-bd02-c746770a4fac",
                    "results":
                        {
                            "open_ended": true,
                            "set": 70,
                            "unset": 30,
                            "categories": [
                                {
                                    "count": 40,
                                    "label": "Food"
                                },
                                {
                                    "count": 10,
                                    "label": "Cake"
                                },
                                {
                                    "count": 15,
                                    "label": "Fruits"
                                },
                                {
                                    "count": 5,
                                    "label": "Coffee"
                                },
                            ]
                        }
                },
                {
                    "id": 17,
                    "title": "Where would you like to eat?",
                    "ruleset_uuid": "e31755dd-c61a-460c-acaf-0eeee1ce0107",
                    "results":
                        {
                            "open_ended": false,
                            "set": 50,
                            "unset": 20,
                            "categories": [
                                {
                                    "count": 30,
                                    "label": "Home"
                                },
                                {
                                    "count": 12,
                                    "label": "Resto"
                                },
                                {
                                    "count": 5,
                                    "label": "Fast Food"
                                },
                                {
                                    "count": 3,
                                    "label": "Other"
                                },
                            ]
                        }
                }
            ],
            "category": {
                "image_url": "http://test.ureport.in/media/categories/StraightOuttaSomewhere_2.jpg",
                "name": "tests"
            },
            "created_on": "2015-09-02T08:53:30.313251Z"
        }
    """

    serializer_class = PollReadSerializer
    queryset = Poll.objects.filter(is_active=True)


class DashboardDetails(RetrieveAPIView):
    """
    This endpoint allows you to get a dashboard data from org.

    ## Get dashboard data

    Example:

        GET /api/v1/dashboard/1/

        Query params:
            card=
                sdg_tracked,
                message_metrics,
                channel_most_used,
                rapidpro_contacts
            filter_by=
                week,
                month,
                year,
                inception
            uuid=123456abcd (only message_metrics)

        Example:
            /api/v1/dashboard/1/?card=message_metrics&filter_by=month
    """
    queryset = Org.objects.filter(is_active=True)
    serializer_class = OrgReadSerializer

    def retrieve(self, request, *args, **kwargs):
        self.access_level = "local"
        data = DashboardDataView.get(self, request=request)
        return Response(json.loads(data.content), content_type="json")

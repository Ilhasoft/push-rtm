# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json

import six
from dash.orgs.models import Org
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from ureport.polls.models import Poll


def generate_absolute_url_from_file(request, file):
    return request.build_absolute_uri(file.url)


class OrgReadSerializer(serializers.ModelSerializer):
    logo_url = SerializerMethodField()
    gender_stats = SerializerMethodField()
    age_stats = SerializerMethodField()
    registration_stats = SerializerMethodField()
    occupation_stats = SerializerMethodField()
    reporters_count = SerializerMethodField()
    timezone = SerializerMethodField()

    class Meta:
        model = Org
        fields = (
            "id",
            "logo_url",
            "name",
            "language",
            "subdomain",
            "domain",
            "timezone",
            "gender_stats",
            "age_stats",
            "registration_stats",
            "occupation_stats",
            "reporters_count",
        )

    def get_logo_url(self, obj):
        if obj.logo:
            return generate_absolute_url_from_file(self.context["request"], obj.logo)
        return None

    def get_gender_stats(self, obj):
        return obj.get_gender_stats()

    def get_age_stats(self, obj):
        return json.loads(obj.get_age_stats())

    def get_registration_stats(self, obj):
        return json.loads(obj.get_registration_stats())

    def get_occupation_stats(self, obj):
        return json.loads(obj.get_occupation_stats())

    def get_reporters_count(self, obj):
        return obj.get_reporters_count()

    def get_timezone(self, obj):
        return six.text_type(obj.timezone)


class PollReadSerializer(serializers.ModelSerializer):
    questions = SerializerMethodField()

    class Meta:
        model = Poll
        fields = ("id", "flow_uuid", "title", "org", "poll_date", "created_on", "questions")

    def get_questions(self, obj):
        questions = []
        for question in obj.get_questions():
            results_dict = dict(open_ended=question.is_open_ended())
            results = question.get_results()
            if results:
                results_dict = results[0]
            results_by_age = question.get_results(segment=dict(age="Age"))
            results_by_gender = question.get_results(segment=dict(gender="Gender"))
            results_by_state = question.get_results(segment=dict(location="State"))
            questions.append(
                {
                    "id": question.pk,
                    "ruleset_uuid": question.ruleset_uuid,
                    "title": question.title,
                    "results": results_dict,
                    "results_by_age": results_by_age,
                    "results_by_gender": results_by_gender,
                    "results_by_location": results_by_state,
                }
            )

        return questions

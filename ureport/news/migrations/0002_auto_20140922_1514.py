# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [("news", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="newsitem",
            name="category",
            field=models.ForeignKey(
                related_name="news", to="categories.Category", help_text="The category this item belongs to"
            ),
        ),
        migrations.AlterField(
            model_name="newsitem",
            name="created_by",
            field=models.ForeignKey(
                related_name="news_newsitem_creations",
                to=settings.AUTH_USER_MODEL,
                help_text="The user which originally created this item",
            ),
        ),
        migrations.AlterField(
            model_name="newsitem",
            name="modified_by",
            field=models.ForeignKey(
                related_name="news_newsitem_modifications",
                to=settings.AUTH_USER_MODEL,
                help_text="The user which last modified this item",
            ),
        ),
        migrations.AlterField(
            model_name="video",
            name="category",
            field=models.ForeignKey(
                related_name="videos", to="categories.Category", help_text="The category this item belongs to"
            ),
        ),
        migrations.AlterField(
            model_name="video",
            name="created_by",
            field=models.ForeignKey(
                related_name="news_video_creations",
                to=settings.AUTH_USER_MODEL,
                help_text="The user which originally created this item",
            ),
        ),
        migrations.AlterField(
            model_name="video",
            name="modified_by",
            field=models.ForeignKey(
                related_name="news_video_modifications",
                to=settings.AUTH_USER_MODEL,
                help_text="The user which last modified this item",
            ),
        ),
    ]

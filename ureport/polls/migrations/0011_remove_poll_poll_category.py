# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("polls", "0010_auto_20140820_1629")]

    operations = [migrations.RemoveField(model_name="poll", name="poll_category")]

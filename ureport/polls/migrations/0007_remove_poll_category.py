# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0006_auto_20140820_1552'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='category',
        ),
    ]

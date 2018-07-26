# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.cache import cache
from django.db import migrations

from ureport.utils import prod_print

# language=SQL
CLEAR_CONTACT_SQL = """
TRUNCATE contacts_contact;

"""


def remove_cache_and_lock_keys(apps, schema_editor):
    try:
        # clear redis cache and locks to allow the next task to fetch all the contacts
        cache.delete_pattern("last:fetch_contacts:*")
        cache.delete_pattern("fetch_contacts")
        cache.delete_pattern("fetch_contacts*")

        prod_print("Removed all cache and lock keys for fetch contacts")

    except AttributeError as e:
        prod_print(e)


class Migration(migrations.Migration):

    dependencies = [("contacts", "0006_auto_20151007_1358")]

    operations = [migrations.RunSQL(CLEAR_CONTACT_SQL), migrations.RunPython(remove_cache_and_lock_keys)]

# Generated by Django 2.2.5 on 2019-10-18 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flowhub', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flow',
            name='stars',
        ),
    ]
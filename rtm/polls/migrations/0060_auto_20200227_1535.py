# Generated by Django 2.2.5 on 2020-02-27 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0059_auto_20200227_1517"),
    ]

    operations = [
        migrations.AlterField(
            model_name="poll",
            name="title",
            field=models.CharField(help_text="The title for this Poll", max_length=255),
        ),
    ]

# Generated by Django 2.2.5 on 2020-01-28 13:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orgs', '0026_fix_org_config_rapidpro'),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogPermissionUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('org', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='logs_permission_unct', to='orgs.Org')),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='logs_permission', to='auth.Group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='logs_permission_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
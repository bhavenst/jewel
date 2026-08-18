# AAP-85084: Custom 2.6 migration for the health check interval default change.
# On devel/2.7 the same AlterField lives in 0025_servicecluster_health_check_interval_default
# (depending on 0024). This migration uses a different name and chains off the 2.6 leaf (0022)
# because migrations 0018-0024 were not backported to 2.6.
#
# Upgrade path (2.6→2.7): Django skips applied migrations not present in the
# current graph ("If the migration is unknown, skip it" — loader.py
# check_consistent_history). This record becomes a harmless orphan in
# django_migrations. The 2.7 version (0025) also runs and is idempotent.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('aap_gateway_api', '0022_usersessionmembership'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicecluster',
            name='health_check_interval_seconds',
            field=models.PositiveIntegerField(default=30, help_text='The time between health check requests.'),
        ),
    ]

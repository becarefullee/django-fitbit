# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fitapp', '0002_initial_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timeseriesdata',
            options={'get_latest_by': 'date'},
        ),
    ]

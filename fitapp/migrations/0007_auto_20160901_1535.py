# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitapp', '0006_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeseriesdatatype',
            name='category',
            field=models.IntegerField(choices=[(0, 'foods'), (1, 'activities'), (2, 'sleep'), (3, 'body')]),
        ),
    ]

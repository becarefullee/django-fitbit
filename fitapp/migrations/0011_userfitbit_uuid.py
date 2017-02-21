# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitapp', '0010_auto_20170210_1026'),
    ]

    operations = [
        migrations.AddField(
            model_name='userfitbit',
            name='uuid',
            field=models.CharField(default=None, max_length=32, null=True),
        ),
    ]

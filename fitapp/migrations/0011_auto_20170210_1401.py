# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitapp', '0010_auto_20170210_1026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeseriesdata',
            name='user',
            field=models.ForeignKey(help_text="The data's user", to='player.Individual'),
        ),
        migrations.AlterField(
            model_name='userfitbit',
            name='user',
            field=models.OneToOneField(to='player.Individual', help_text='The user'),
        ),
    ]

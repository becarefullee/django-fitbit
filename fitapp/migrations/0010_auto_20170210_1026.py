# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitapp', '0009_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeseriesdata',
            name='date',
            field=models.DateTimeField(help_text='The date the data was recorded'),
        ),
        migrations.AlterField(
            model_name='timeseriesdata',
            name='resource_type',
            field=models.ForeignKey(help_text='The type of time series data', to='fitapp.TimeSeriesDataType'),
        ),
        migrations.AlterField(
            model_name='timeseriesdata',
            name='user',
            field=models.ForeignKey(help_text="The data's user", to='fitapp.TestUserModel'),
        ),
        migrations.AlterField(
            model_name='timeseriesdata',
            name='value',
            field=models.CharField(default=None, null=True, max_length=32, help_text='The value of the data. This is typically a number, though saved as a string here. The units can be inferred from the data type. For example, for step data the value might be "9783" (the units) would be "steps"'),
        ),
        migrations.AlterField(
            model_name='timeseriesdatatype',
            name='category',
            field=models.IntegerField(choices=[(0, 'foods'), (1, 'activities'), (2, 'sleep'), (3, 'body')], help_text='The category of the time series data, one of: 0(foods), 1(activities), 2(sleep), 3(body)'),
        ),
        migrations.AlterField(
            model_name='timeseriesdatatype',
            name='resource',
            field=models.CharField(help_text='The specific time series resource. This is the string that will be used for the [resource-path] of the API url referred to in the Fitbit documentation', max_length=128),
        ),
        migrations.AlterField(
            model_name='userfitbit',
            name='access_token',
            field=models.TextField(help_text='The OAuth2 access token'),
        ),
        migrations.AlterField(
            model_name='userfitbit',
            name='expires_at',
            field=models.FloatField(help_text='The timestamp when the access token expires'),
        ),
        migrations.AlterField(
            model_name='userfitbit',
            name='fitbit_user',
            field=models.CharField(unique=True, help_text='The fitbit user ID', max_length=32),
        ),
        migrations.AlterField(
            model_name='userfitbit',
            name='refresh_token',
            field=models.TextField(help_text='The OAuth2 refresh token'),
        ),
        migrations.AlterField(
            model_name='userfitbit',
            name='user',
            field=models.OneToOneField(to='fitapp.TestUserModel', help_text='The user'),
        ),
    ]

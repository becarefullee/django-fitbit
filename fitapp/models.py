import logging
import uuid
from base64 import urlsafe_b64encode

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

logger = logging.getLogger(__name__)

UserModel = getattr(settings, 'FITAPP_USER_MODEL', 'auth.User')


@python_2_unicode_compatible
class UserFitbit(models.Model):
    """
    A user's fitbit credentials, allowing API access

    WARNING: Changes to the user field should be made manually to the
    0001_initial migration
    """
    user = models.OneToOneField(
        UserModel, help_text='The user')
    fitbit_user = models.CharField(
        max_length=32, unique=True, help_text='The fitbit user ID')
    access_token = models.TextField(help_text='The OAuth2 access token')
    refresh_token = models.TextField(help_text='The OAuth2 refresh token')
    expires_at = models.FloatField(
        help_text='The timestamp when the access token expires')
    # This url-safe uuid is to allow non-conflicting subscription ids
    uuid = models.CharField(max_length=32, default=None, null=True)

    def __str__(self):
        return self.user.__str__()

    def refresh_cb(self, token):
        """ Called when the OAuth token has been refreshed """
        self.access_token = token['access_token']
        self.refresh_token = token['refresh_token']
        self.expires_at = token['expires_at']
        self.save()

    def get_user_data(self):
        return {
            'user_id': self.fitbit_user,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at,
            'refresh_cb': self.refresh_cb,
            'uuid': self.uuid,
        }

    def get_subscriptions(self):
        """
        Return a list of the subscriptions in the project's collection list that exist for the UFB.

        This is needed because a call to the Fitbit API can only return subscriptions for one
        collection at a time, or it attempts to return subscriptions for all possible collections,
        which causes an unauthorized error if a project doesn't have access to all collections.
        """
        from .utils import create_fitbit, get_setting

        fb = create_fitbit(**self.get_user_data())
        collections = get_setting('FITAPP_SUBSCRIPTION_COLLECTION')
        if isinstance(collections, str):
            collections = [collections]

        subscriptions = []

        for collection in collections:
            try:
                subscriptions.extend(
                    fb.list_subscriptions(collection=collection)['apiSubscriptions'])
            except Exception as e:
                logger.exception(e)
                subscriptions.append(
                    'An error occurred while listing subscriptions '
                    'for the {} collection'.format(collection))

        return subscriptions

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = urlsafe_b64encode(uuid.uuid4().bytes)[:22]
        return super(UserFitbit, self).save(*args, **kwargs)


class TimeSeriesDataType(models.Model):
    """
    This model is intended to store information about Fitbit's time series
    resources, documentation for which can be found here:
    https://dev.fitbit.com/docs/food-logging/#food-or-water-time-series
    https://dev.fitbit.com/docs/activity/#activity-time-series
    https://dev.fitbit.com/docs/sleep/#sleep-time-series
    https://dev.fitbit.com/docs/body/#body-time-series
    """

    foods = 0
    activities = 1
    sleep = 2
    body = 3
    CATEGORY_CHOICES = (
        (foods, 'foods'),
        (activities, 'activities'),
        (sleep, 'sleep'),
        (body, 'body'),
    )
    intraday_support = models.BooleanField(default=False)
    category = models.IntegerField(
        choices=CATEGORY_CHOICES,
        help_text='The category of the time series data, one of: {}'.format(
            ', '.join(['{}({})'.format(ci, cs) for ci, cs in CATEGORY_CHOICES])
        ))
    resource = models.CharField(
        max_length=128,
        help_text=(
            'The specific time series resource. This is the string that will '
            'be used for the [resource-path] of the API url referred to in '
            'the Fitbit documentation'
        ))

    def __str__(self):
        return self.path()

    class Meta:
        unique_together = ('category', 'resource',)
        ordering = ['category', 'resource']

    def path(self):
        return '/'.join([self.get_category_display(), self.resource])


class TimeSeriesData(models.Model):
    """
    The purpose of this model is to store Fitbit user data obtained from their
    time series API (https://wiki.fitbit.com/display/API/API-Get-Time-Series).

    Intraday data only: user's timezone is retrieved and used to convert data to
    UTC prior to saving.
    time series API:
    https://dev.fitbit.com/docs/food-logging/#food-or-water-time-series
    https://dev.fitbit.com/docs/activity/#activity-time-series
    https://dev.fitbit.com/docs/sleep/#sleep-time-series
    https://dev.fitbit.com/docs/body/#body-time-series

    WARNING: Changes to the user field should be made manually to the
    0001_initial migration
    """
    user = models.ForeignKey(UserModel, help_text="The data's user")
    resource_type = models.ForeignKey(
        TimeSeriesDataType, help_text='The type of time series data')
    date = models.DateTimeField(help_text='The date the data was recorded')
    value = models.CharField(
        null=True,
        default=None,
        max_length=32,
        help_text=(
            'The value of the data. This is typically a number, though saved '
            'as a string here. The units can be inferred from the data type. '
            'For example, for step data the value might be "9783" (the units) '
            'would be "steps"'
        ))
    intraday = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'resource_type', 'date', 'intraday')
        get_latest_by = 'date'

    def string_date(self):
        return self.date.strftime('%Y-%m-%d')


class TestUserModel(models.Model):
    pass


class SleepStageTimeSeriesData(models.Model):
    """
    This model is intended to store sleep stage logs obtained from Fitbit API
    
    Sleep log API:
    https://dev.fitbit.com/build/reference/web-api/sleep/
    """
    user = models.ForeignKey(UserModel, help_text="The data's user")
    date = models.DateTimeField(help_text='The date and time the data was recorded')
    level = models.CharField(null=False, max_length=32, help_text='Sleep stages')
    seconds = models.IntegerField(help_text='The amount of time last for this sleep period')

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
        get_latest_by = 'date'

    def __str__(self):
        if self.level == 'wake':
            return '{user} is awake from {date} last {seconds} seconds'.format(
                user=self.user, date=self.date, level=self.level, seconds=self.seconds
            )
        else:
            return '{user} is {level} sleep start from {date} last {seconds} seconds.'.format(
                user=self.user, date=self.date, level=self.level, seconds=self.seconds
            )


class SleepStageSummary(models.Model):
    """
    This model is intended to store the summary of sleep stage logs.
    
    This model has a one to many relationship to SleepTypeData. In fact, every valid 
    SleepStageSummary instance should has four different SleepTypeData which represents 
    the summary of wake/rem/light/deep level's sleep log.
    """
    user = models.ForeignKey(UserModel, help_text="The data's user")
    date = models.DateTimeField(help_text='The date the data was recorded')

    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'date')

    def __str__(self):
        return "{user}'s sleep summary on {year}-{month}-{day}".format(
            user=self.user, year=self.date.year, month=self.date.month, day=self.date.day)

    @property
    def get_summary_data(self):
        return list(SleepTypeData.objects.filter(sleep_summary=self))


class SleepTypeData(models.Model):
    """
    This model is intended to store the summary of a certain level(wake/rem/light/deep) sleep log.
    
    Each SleepTypeData instance will associate with a SleepStageSummary instance to represent as the 
     summary of a certain level's sleep for a user on some day.
    """
    sleep_summary = models.ForeignKey(SleepStageSummary,
                                      help_text='The summary object that this sleep associated with')
    level = models.CharField(null=False, max_length=32, help_text='Sleep stages')
    count = models.IntegerField(help_text='Number of this type of sleep status')
    minute = models.IntegerField(help_text='How long this type of sleep last in total')

    class Meta:
        unique_together = ('sleep_summary', 'level')
        ordering = ['sleep_summary']

    def __str__(self):
        return "{user}'s {level} level summary on {year}-{month}-{day}".format(
            user=self.sleep_summary.user,
            level=self.level, year=self.sleep_summary.date.year,
            month=self.sleep_summary.date.month, day=self.sleep_summary.date.day)

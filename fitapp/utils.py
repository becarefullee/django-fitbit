import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from fitbit import Fitbit
from fitbit.exceptions import HTTPBadRequest, HTTPTooManyRequests, HTTPUnauthorized

from . import defaults
from .models import UserFitbit, TimeSeriesDataType, SleepStageTimeSeriesData,\
    SleepStageSummary, SleepTypeData


def create_fitbit(consumer_key=None, consumer_secret=None, **kwargs):
    """Shortcut to create a Fitbit instance.

    If consumer_key or consumer_secret are not provided, then the values
    specified in settings are used.
    """
    if consumer_key is None:
        consumer_key = get_setting('FITAPP_CONSUMER_KEY')
    if consumer_secret is None:
        consumer_secret = get_setting('FITAPP_CONSUMER_SECRET')

    if consumer_key is None or consumer_secret is None:
        raise ImproperlyConfigured(
            "Consumer key and consumer secret cannot "
            "be null, and must be explicitly specified or set in your "
            "Django settings"
        )
    fitbit = Fitbit(consumer_key, consumer_secret, **kwargs)
    fitbit.API_VERSION = 1.2
    return fitbit


def is_integrated(user):
    """Returns ``True`` if we have Oauth info for the user.

    This does not require that the token and secret are valid.

    :param user: A Django User.
    """
    return UserFitbit.objects.filter(user=user).exists()


def get_valid_periods():
    """Returns list of periods for which one may request time series data."""
    return ['1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max']


def get_fitbit_data(fbuser, resource_type, base_date=None, period=None,
                    end_date=None, return_all=False):
    """Creates a Fitbit API instance and retrieves step data for the period.

    Several exceptions may be thrown:
        TypeError           - Either end_date or period must be specified, but
                              not both.
        ValueError          - Invalid argument formats.
        HTTPUnauthorized    - 401 - fbuser has bad authentication credentials.
        HTTPForbidden       - 403 - This isn't specified by Fitbit, but does
                                 appear in the Python Fitbit library.
        HTTPNotFound        - 404 - The specific resource doesn't exist.
        HTTPConflict        - 409 - HTTP conflict
        HTTPTooManyRequests - 429 - Hitting the rate limit
        HTTPServerError     - >=500 - Fitbit server error or maintenance.
        HTTPBadRequest      - >=400 - Bad request.
    """
    fb = create_fitbit(**fbuser.get_user_data())
    resource_path = resource_type.path()
    print(resource_path)
    data = fb.time_series(resource_path, user_id=fbuser.fitbit_user,
                          period=period, base_date=base_date,
                          end_date=end_date)
    if return_all:
        return data
    return data[resource_path.replace('/', '-')]


def get_fitbit_profile(fbuser, key=None):
    """
    Creates a Fitbit API instance and retrieves a user's profile.
    """
    fb = create_fitbit(**fbuser.get_user_data())
    data = fb.user_profile_get()

    data = data['user']
    if key:
        return data[key]
    return data


def get_setting(name, use_defaults=True):
    """Retrieves the specified setting from the settings file.

    If the setting is not found and use_defaults is True, then the default
    value specified in defaults.py is used. Otherwise, we raise an
    ImproperlyConfigured exception for the setting.
    """
    if hasattr(settings, name):
        return _verified_setting(name)
    if use_defaults:
        if hasattr(defaults, name):
            return getattr(defaults, name)
    msg = "{0} must be specified in your settings".format(name)
    raise ImproperlyConfigured(msg)


def _verified_setting(name):
    result = getattr(settings, name)
    if name == 'FITAPP_SUBSCRIPTIONS':
        # Check that the subscription list is valid
        try:
            items = result.items()
        except AttributeError:
            msg = '{} must be a dict or an OrderedDict'.format(name)
            raise ImproperlyConfigured(msg)
        # Only make one query, which will be cached for later use
        all_tsdt = list(TimeSeriesDataType.objects.all())
        for cat, res in items:
            tsdts = list(filter(lambda t: t.get_category_display() == cat, all_tsdt))
            if not tsdts:
                msg = '{} is an invalid category'.format(cat)
                raise ImproperlyConfigured(msg)
            all_cat_res = set(map(lambda tsdt: tsdt.resource, tsdts))
            if set(res) & all_cat_res != set(res):
                msg = '{0} resources are invalid for the {1} category'.format(
                    list(set(res) - (set(res) & all_cat_res)), cat)
                raise ImproperlyConfigured(msg)
    return result


def get_all_sleep_log(date):
    """
    Get all user's sleep log at a certain date.
    
    :param date: The date of the sleep log (datetime).
    
    Throw exceptions if an error occurs during the request. 
    """
    fbusers = UserFitbit.objects.all()
    print('Fitbit Users: {}'.format(fbusers))
    try:
        for fbuser in fbusers:
            get_fitbit_sleep_log(fbuser=fbuser, date=date)
    except HTTPTooManyRequests:
        # We have hit the rate limit for the user, retry when it's reset,
        # according to the reply from the failing API call
        print('Rate limit reached for user {}'.format(fbuser))
    except HTTPBadRequest:
        # If the resource is elevation or floors, we are just getting this
        # error because the data doesn't exist for this user, so we can ignore
        # the error
        e = sys.exc_info()[1]
        print('Bad request: {}'.format(e))
    except Exception:
        e = sys.exc_info()[1]
        print('Exception: {}'.format(e))


def get_sleep_log_by_date_range(fbuser, start_date, end_date):
    """
    Get the sleep logs of a user during a date range.
    
    :param fbuser: A UserFitbit instance (UserFitbit).
    :param start_date: sleep logs start date (datetime).
    :param end_date: sleep logs end date (datetime).
    """
    fb = create_fitbit(**fbuser.get_user_data())
    start_date_string = fb._get_date_string(start_date)
    end_date_string = fb._get_date_string(end_date)
    url = "{0}/{1}/user/-/sleep/date/" \
          "{start_date}/{end_date}.json" \
        .format(*fb._get_common_args(),
                start_date=start_date_string,
                end_date=end_date_string
                )
    data = fb.make_request(url)
    parse_sleep_data(fbuser=fbuser, json_data=data)


def get_fitbit_sleep_log(fbuser, date, summary=False):
    """
    This method calls get_sleep(date) method of a Fitbit instance to get the sleep log, 
    parse the json data and save it to database after that. This method can be used to get either sleep time 
    series data or the sleep summary log if summary param is True.
    
    :param fbuser: A UserFitbit instance (UserFitbit).
    :param date: The date of the log (datetime).
    :param summary: Whether it should be a sleep summary data, set False by default (Bool).
    """
    fb = create_fitbit(**fbuser.get_user_data())
    data = fb.get_sleep(date)
    parse_sleep_data(fbuser=fbuser, json_data=data, summary=summary)


def parse_sleep_data(fbuser, json_data, summary=False):
    """
    Parse the json data get from Fitbit API, if the data is valid, save it to database.
    
    :param fbuser: A UserFibit instance (UserFitbit).
    :param json_data: Json data that get from Fitbit API 
    :param summary: Whether it should be a sleep summary data, set False by default (Bool).
    """
    sleep_data = json_data['sleep']
    if sleep_data:
        for intraday in sleep_data:
            date_of_sleep = intraday['dateOfSleep']
            if summary:
                summary_data = intraday['levels']['summary']
                keys = ['wake', 'rem', 'light', 'deep']
                sleep_summary_object, _ = SleepStageSummary.objects.get_or_create(user=fbuser.user, date=date_of_sleep)
                sleep_summary_object.save()
                for key in keys:
                    count = summary_data[key]['count'] if summary_data[key]['count'] else 0
                    minute = summary_data[key]['minutes'] if summary_data[key]['minutes'] else 0
                    sleep_summary_data, created = SleepTypeData.objects.get_or_create(
                        sleep_summary=sleep_summary_object, level=key, count=count, minute=minute)
                    sleep_summary_data.save()
            else:
                short_data = intraday['levels']['data']
                for data in short_data:
                    # Create new record or update existing
                    sleep_time_series_data, created = SleepStageTimeSeriesData.objects.get_or_create(
                        user=fbuser.user, date=data['dateTime'],
                        level=data['level'], seconds=data['seconds'])
                    sleep_time_series_data.save()

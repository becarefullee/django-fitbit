"""
This django management command can be used to run basic diagnostics on a
UserFitbit object

A username referring to UserFitbit.user.username must be included when calling
this command.
"""

import pprint

from django.core.management.base import BaseCommand
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from fitapp.models import UserFitbit, TimeSeriesDataType
from fitapp.utils import create_fitbit
from fitapp.tasks import get_time_series_data


class Command(BaseCommand):
    help = """
        Runs basic UserFitbit diagnostics for a given user.
        """

    def add_arguments(self, parser):
                parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']

        user_fitbits = UserFitbit.objects.filter(user__username=username)
        if not user_fitbits:
            print("No UserFitbit objects associated with the "
                  "given username: {}".format(username))
            return

        if user_fitbits.count() > 1:
            print("Multile UserFitbit objects found for "
                  "username: {}".format(username))
            return

        user_fitbit = user_fitbits.first()

        print("GENERAL DETAILS:")
        pprint.pprint(user_fitbit.get_user_data())

        fitbit = create_fitbit(**user_fitbit.get_user_data())

        print("\nACCESS TOKEN DETAILS:")
        try:
            fitbit.client.refresh_token()
            print("Successfully refreshed access token.")
            user_fitbit.refresh_from_db()
            print("New access token expires at: {}".format(
                user_fitbit.expires_at))
        except InvalidGrantError:
            print("INVALID GRANT ERROR: could not refresh access token.")
            return

        print("\nDEVICES:")
        for device in fitbit.get_devices():
            pprint.pprint(device)

        print("\nSUBSCRIPTIONS:")
        pprint.pprint(fitbit.list_subscriptions(collection='activities'))

        print("\nPULLING STEP DATA:")
        tsd = TimeSeriesDataType.objects.get(
            category=TimeSeriesDataType.activities, resource="steps")
        try:
            get_time_series_data(user_fitbit.fitbit_user,
                                 tsd.category, tsd.resource)
            print("Successfully pulled step data.")
        except Exception as e:
            print("Exception pulling fitbit data: {}".format(e))

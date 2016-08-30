# Your Fitbit access credentials, which must be requested from Fitbit.
# You must provide these in your project's settings.
FITAPP_CONSUMER_KEY = None
FITAPP_CONSUMER_SECRET = None

# The verification code for verifying subscriber endpoints
FITAPP_VERIFICATION_CODE = None

# Where to redirect to after Fitbit authentication is successfully completed.
FITAPP_LOGIN_REDIRECT = '/'

# Where to redirect to after Fitbit authentication credentials have been
# removed.
FITAPP_LOGOUT_REDIRECT = '/'

# By default, don't subscribe to user data. Set this to true to subscribe.
FITAPP_SUBSCRIBE = False

# By default, don't try to get intraday time series data. See
# https://dev.fitbit.com/docs/activity/#get-activity-intraday-time-series for
# more info.
FITAPP_GET_INTRADAY = False

# The verification code used by Fitbit to verify subscription endpoints. Only
# needed temporarily. See:
# https://dev.fitbit.com/docs/subscriptions/#verify-a-subscriber
FITAPP_VERIFICATION_CODE = None

# The template to use when an unavoidable error occurs during Fitbit
# integration.
FITAPP_ERROR_TEMPLATE = 'fitapp/error.html'

# The default message used by the fitbit_integration_warning decorator to
# inform the user about Fitbit integration. If a callable is given, it is
# called with the request as the only parameter to get the final value for the
# message.
FITAPP_DECORATOR_MESSAGE = 'This page requires Fitbit integration.'

# Whether or not a user must be authenticated in order to hit the login,
# logout, error, and complete views.
FITAPP_LOGIN_REQUIRED = True

# Whether or not intraday data points with step values of 0 are saved
# to the database.
FITAPP_SAVE_INTRADAY_ZERO_VALUES = False

# The default amount of data we pull for each user registered with this app
FITAPP_DEFAULT_PERIOD = 'max'

# The default fitbit scope, None defaults to all scopes, otherwise take
# a list of scopes (eg. ["activity", "profile", "settings"])
FITAPP_SCOPE = None

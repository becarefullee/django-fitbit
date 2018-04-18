from django.contrib import admin
from django.conf.urls import patterns
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render

from . import models
from . import forms
from . import utils


class UserFitbitAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for UserFitbit so that associations can be made via the
    admin site.
    """
    def get_urls(self):
        """
        Add a custom pattern so that the new view can be accessed.

        Note that custom patterns are included before the regular admin URLs.
        """
        urls = super(UserFitbitAdmin, self).get_urls()
        associate_url = patterns('',
            (r'^associate/$', self.admin_site.admin_view(
                self.associate_userfitbit))
        )
        return associate_url + urls

    def associate_userfitbit(self, request):
        """
        Associate a UserFitbit to the user_model defined in the settings, via
        the admin interface.
        """
        user_model = models.UserFitbit.user.field
        if request.method == 'POST':
            form = forms.UserFitbitForm(request.POST)
            to_assoc = user_model.rel.to.objects.filter(pk=int(request.POST.
                                                               get('user')))
            form.fields['user'].queryset = to_assoc
            if form.is_valid():
                user = form.cleaned_data['user']
                # Stuff the user's pk for the 'complete' view
                request.session['fb_user_id'] = user.pk
                return redirect(reverse('fitbit-login'))
        else:
            # Only show the users that do not have an associated Fitbit
            user_fitbits = models.UserFitbit.objects.all()
            associated = [ufb.user.pk for ufb in user_fitbits]
            unassociated = user_model.rel.to.objects.exclude(pk__in=associated)
            # Now use them as the options for the (unbound) form
            form = forms.UserFitbitForm()
            form.fields['user'].queryset = unassociated
            return render(request,
                          'admin/fitapp/userfitbit/associate.html',
                          {'form': form})
        return render(request, utils.get_setting('FITAPP_ERROR_TEMPLATE'), {})

admin.site.register(models.UserFitbit, UserFitbitAdmin)
admin.site.register(models.TimeSeriesDataType)
admin.site.register(models.TimeSeriesData)
admin.site.register(models.SleepStageTimeSeriesData)
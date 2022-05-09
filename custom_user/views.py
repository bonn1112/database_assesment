from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, HttpResponseRedirect
from django.urls import reverse


class CustomLoginView(LoginView):
    form_class = AuthenticationForm

    def post(self, request, *args, **kwargs):
        """
        user authenticate and redirect each user's role

        Args:
            request (any): request from view

        Returns:
            if user's role is admin, redirect admin page
            if user's role is to manage bb product database, redirect bb product page
            if user's role is to manage population database, redirect population page
        """
        form = self.get_form()
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request=request, username=username, password=password)
            login(request, user)
            if user.db_role == 0:
                return redirect('/admin/')
            if user.db_role == 1:
                return HttpResponseRedirect(reverse('bb_product'))
            if user.db_role == 2:
                return HttpResponseRedirect(reverse('populations'))
        else:
            return self.form_invalid(form)

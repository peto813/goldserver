
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from gold_admin.models import *
# from allauth.account.utils import send_email_confirmation
from django.utils.translation import gettext, gettext_lazy as _

class UserCreateForm(UserCreationForm):
	role_choices = (
		('admin', _('Admin')),
		('client', _('Client')),
	)
	first_name = forms.CharField(required= True)
	last_name = forms.CharField(required= True)
	role = forms.ChoiceField(choices=role_choices, required = True)

	class Meta:
		model = User
		fields = ('username', 'first_name' , 'last_name','role', )

	def save(self, commit=True):
		instance = super(UserCreateForm, self).save(commit=False)
		role = self.data.get('role', None)
		if role=='client':
			instance.save()
			#userprofile, created= UserProfile.objects.get_or_create(user=instance)
		elif role=='admin':
			instance.is_staff= True
			instance.is_superuser= True
			instance.save()
		return instance
# -*- coding: utf-8 -*-
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, mail_admins


class customRegisterAdapter(DefaultAccountAdapter):
	def send_confirmation_mail(self, request, emailconfirmation, signup):
		current_site = get_current_site(request)
		activate_url = self.get_email_confirmation_url( request, emailconfirmation)
		user = emailconfirmation.email_address.user
		ctx = {
			"user": user,
			"activate_url": activate_url,
			"current_site": current_site,
			"key": emailconfirmation.key,
			'full_name': user.first_name.title() +' '+user.last_name.title()
		}
		if signup:
			email_template = 'account/email/new_owner'
		else:
			email_template = 'account/email/new_owner'
		self.send_mail(email_template,emailconfirmation.email_address.email, ctx)
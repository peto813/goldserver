# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _
from gold_admin.models import *
from gold_admin.forms import UserCreateForm
from allauth.account.utils import send_email_confirmation

admin.site.register(UserProfile)

# Register your models here.
class CustomUserAdmin(UserAdmin):
	def save_model(self, request, user, form, change):#ADDITIONAL VALIDATION IN MODEL'S SAVE METHOD IN models.py
		if form.has_changed() and form.is_valid():
			super(CustomUserAdmin, self).save_model(request, user, form, change)
			if form.cleaned_data.get('role')=='client':
				send_email_confirmation(request, user)

	add_form = UserCreateForm
	# prepopulated_fields = {'username': ('first_name' , 'last_name', )}
	#send_email_confirmation(request, instance, signup=False)
	add_fieldsets = (
		(None, {
		'classes': ('wide',),
		'fields': ('email', 'username','first_name', 'last_name', 'password1', 'password2','role' ),
		}),
	)

	list_display = ['id','full_name','email','company_name', 'is_staff']
	actions = [ 'resend_confirmation_email']
	def full_name(self, obj):
		return obj.first_name+' '+ obj.last_name

	# def role(self, obj):
	# 	return obj.userprofile.role.name

	def company_name(self, obj):
		return obj.userprofile.company.name

    
	def resend_confirmation_email(self, request, queryset):
		for user in queryset:
			if not user.is_staff and not user.is_superuser:
				send_email_confirmation(request, user)

	resend_confirmation_email.short_description = _("Resend confirmation E-mail")
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class RolesInline(admin.TabularInline):
	model = UserProfile.company.through
	verbose_name = _("Owner")
	verbose_name_plural =  _("Owners")
	fields = ("user","name")
	extra = 0

	fields = ["get_role", "user"]
	readonly_fields = ["get_role"]

	def get_role(self, obj=None):
		return _("owner")
	get_role.short_description = _("Role")
	get_role.allow_tags = True



	show_change_link = True

class CompanydAdmin( admin.ModelAdmin ):
	list_filter = ('country__name',)
	inlines =(RolesInline,)
	fields = [ 'name', 'id_number','mobile', 'office', 'other_number', 'address', 'country']
	list_display = ['id', 'name','mobile', 'office','other_number', 'country' ]

	def save_model(self, request, user, form, change):#ADDITIONAL VALIDATION IN MODEL'S SAVE METHOD IN models.py
		if form.is_valid():
			instance=super(CompanydAdmin, self).save_model(request, user, form, change)
			if form.cleaned_data.get('role')=='client':
				role, created=Role.objects.get_or_create(user = user, company= instance, name= 'owner')
				send_email_confirmation(request, user)

admin.site.register(Company, CompanydAdmin)

class RoledAdmin( admin.ModelAdmin ):
	# list_filter = ('country__name',)
	# inlines =(OwnersInline,)
	# fields = [ 'name', 'id_number','mobile', 'office', 'other_number', 'address', 'country']

    # def save_model(self, request, obj, form, change):#ADDITIONAL VALIDATION IN MODEL'S SAVE METHOD IN models.py
    #     if form.has_changed() and form.is_valid():
    #         super(RoledAdmin, self).save_model(request, obj, form, change)
    #         send_email_confirmation(request, obj.user)

	list_display = ['id', 'name' , 'user']
admin.site.register(Role, RoledAdmin)

class CountryAdmin( admin.ModelAdmin ):
	pass
    #inlines = (Payment_MethodInline,)
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    #list_display = ['nombre', 'moneda', 'nombre_registro_fiscal','activo', 'rif_regex']
admin.site.register( Country, CountryAdmin )



class AccountAdmin( admin.ModelAdmin ):
    #inlines = (Payment_MethodInline,)
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    def moneda(self, obj):
        return smart_unicode(obj.account_type.name.title())
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    readonly_fields = ('moneda',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = [ 'id','moneda','created', 'role', 'start_balance', 'balance']
admin.site.register( Account, AccountAdmin )

class AccountTypeAdmin( admin.ModelAdmin ):
    #inlines = (Payment_MethodInline,)
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['name', 'currency_nick']
admin.site.register( AccountType, AccountTypeAdmin )


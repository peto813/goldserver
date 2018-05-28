# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext, gettext_lazy as _
from django.utils.encoding import smart_unicode
#from django.core.mail import send_mail, send_mass_mail, mail_admins, EmailMessage, EmailMultiAlternatives, get_connection
from django.conf import settings
from django.db.models.signals import post_delete, pre_delete, post_save, pre_save
from gold_admin.utils import massToGrams
from gold_admin.managers import TransactionManager
from django.contrib.auth.signals import user_logged_in
#signal methods



# def set_session(sender, user, request, **kwargs):
# 	#find if user is only tied to one company
# 	companies =user.userprofile.companies
# 	if companies.count()==1:
# 		request.session['company_id'] = companies.first().id

# user_logged_in.connect(set_session)


def transaction_post_save(sender, instance, created,**kwargs):

	'''
	signal adapts units to gr when saved
	'''
	if created:
		if instance.tipo =='compra':
			'''
			adjust user gold balance (increases), minimum of three weights
			adjust transaction gold balance (increases)
			adjust user account balance used for purchase (decreases)
			'''
			
			instance.cantidad=massToGrams(instance.cantidad, instance.weightUnit)
			amounts = [instance.cantidad]
			instance.pesoPost=massToGrams(instance.pesoPost, instance.weightUnit)
			instance.pesoPostLegal=massToGrams(instance.pesoPostLegal, instance.weightUnit)

			if instance.pesoPost:
				amounts.append(instance.pesoPost)
			if instance.pesoPostLegal:
				amounts.append(instance.pesoPostLegal)
						
			min_cantidad = min(amounts)
			instance.user.userprofile.gold_balance += min_cantidad
			instance.user.userprofile.save()
			instance.account.balance -= ( (instance.precio * instance.cantidad) + decimal.Decimal(instance.meltCost or 0) + decimal.Decimal(instance.evalCost or 0) )
			instance.account.save()
			instance.balance = instance.user.userprofile.gold_balance
			instance.save()

		if instance.tipo =='venta':
			amounts = [instance.cantidad]

			if instance.pesoPost:
				amounts.append(instance.pesoPost)
			if instance.pesoPostLegal:
				amounts.append(instance.pesoPostLegal)

			min_cantidad = min(amounts)
			instance.user.userprofile.gold_balance -= min_cantidad
			instance.user.userprofile.save()
			instance.balance= instance.user.userprofile.gold_balance
			instance.save()
			instance.account.balance += (instance.precio * min_cantidad)
			instance.account.save()
			buy = instance.related_transaction
			buy.related_transaction	= instance
			buy.save()

	# else:
	# 	if instance.tipo=='abono' and has_changed:
	# 		if instance.approved==False:
	# 			pass
	# 		elif instance.approved==True:
	# 			pass



def acc_type_post_save(sender, instance, created,**kwargs):

	'''
	when account type is created it is generated for each user
	'''
	if created:
		roles= Role.objects.all()
		for role in roles:
			#user_has_new_acount_type(user)
			account, created= Account.objects.get_or_create(role= role,  account_type= instance )

def role_type_post_save(sender, instance, created,**kwargs):

	'''
	when a role is created, created user accounts
	'''
	if created:
		account_types= AccountType.objects.all()
		for account_type in account_types:
			account, created= Account.objects.get_or_create(role= instance,  account_type= account_type )
		# roles= Role.objects.all()
		# for role in roles:
		# 	#user_has_new_acount_type(user)
		# 	account, created= Account.objects.get_or_create(role= role,  account_type= instance )

# roles= Role.objects.all()
# for role in roles:
# 	#user_has_new_acount_type(user)
# 	account, created= Account.objects.get_or_create(role= role,  account_type= self )



# Create your models here.
def upload_picture_path(instance, filename):
	return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.user.id, 'picture', filename ))

class UserProfile(models.Model):
	'''
	a user is either a broker for all related companies 
	or an owner for all related, roles are absolute. 
	Thus, company owners can not broker for other companies.
	'''
	#custom user profile model
	role_choices = (
		('owner', _('Owner')),
		('broker', _('Broker')),
		# ('Reembolso', _('Refund')),
		# ('cobranza', _('Charges/Penalties')),
		# ('Intereses', _('Interest')),
	)
	user = models.OneToOneField(User, null= False, on_delete=models.CASCADE, related_name="userprofile")
	# custom fields for user
	company  = models.ManyToManyField('Company', related_name=_("users"), through='Role')
	#role=models.ForeignKey('Role')
	#company_name = models.CharField(max_length=100)
	location = models.CharField(max_length=250, null= True)
	id_number = models.CharField(max_length=100, verbose_name=_('Fiscal Number'))
	picture = models.ImageField( upload_to = upload_picture_path, default='', null=False, blank= True, help_text=_('You must select a file'), verbose_name = _('fiscal number image'))
	mobile=models.CharField( null= True, blank = True, max_length=15)
	office=models.CharField( null= True, blank = True, max_length=15)
	other=models.CharField( null= True, blank = True, max_length=15)
	gold_balance  = models.DecimalField( null = False, blank = False, decimal_places = 4, max_digits= 50, default= 0)

	@property
	def basic_role(self):
		users_company_roles = self.user.userprofile.company.through.objects.filter(user=self.user.userprofile)
		#print users_company_roles, 'roles'
		user_has_owner_role =users_company_roles.filter(name ='owner').exists()
		#print 'admin' if self.user.is_superuser else ('owner' if user_has_owner_role else 'broker')
		return 'admin' if self.user.is_superuser else ('owner' if user_has_owner_role else 'broker')


	@property
	def companies(self):
		'''
		returns companies related to user regardless of users role
		'''
		#companies = [{'id':item.id, 'name': item.name} for item in self.company.all()]
		return self.company.all()

	@property
	def roles(self):
		'''
		there are three basic roles admin, owner, other
		this function determines the basic user role.

		'''
		#users_company_roles = self.company.through.objects.all()
		#user_has_owner_role =users_company_roles.filter(name ='owner').exists()
		#return 'admin' if self.user.is_superuser else ('owner' if user_has_owner_role else 'broker')
		#print self.company.through.objects.all()
		companies = self.company.through.objects.filter(user=self)
		return companies.filter(user=self)


	def __unicode__(self): #__str__ for python 3.3
		return smart_unicode( self.user.first_name + self.user.last_name)


class Country(models.Model):
	name =  models.CharField( max_length = 80, null=False, blank = False, primary_key = True, unique = True, verbose_name = _('country name') )
	currency  = models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('Currency'), default= '' )
	active = models.BooleanField( default = False, verbose_name = _('Active') )
	country_code = models.CharField( max_length = 5, null=True, blank = True, help_text=_("internationa telephone code") )
	sales_tax = models.DecimalField(help_text=_("0-100%"), max_digits=50, decimal_places=4, verbose_name=_('sales tax'), null= False, default= 0)
	def __unicode__(self): #__str__ for python 3.3
		return smart_unicode( self.name)

class Company(models.Model):
	name = models.CharField(max_length=100, null= False, blank= False)
	id_number = models.CharField(max_length=100, unique=True)
	mobile=models.CharField( null= True, blank = True,max_length=15)
	office=models.CharField( null= True, blank = True,max_length=15)
	other_number=models.CharField( null= True, blank = True,max_length=15)
	address= models.TextField( max_length = 1000, null=False, blank = False, verbose_name = _('company address') )
	country = models.ForeignKey(Country, null = False, verbose_name = _('country'))
	#make a get role method
	def __unicode__(self): #__str__ for python 3.3
		return smart_unicode( self.name)


class Role(models.Model):
	'''
	NOTE: field name "user" should actually be a userprofile model instance
	'''

	role_choices = (
		('owner', _('Owner')),
		('broker', _('Broker')),
	)
	name = models.CharField(choices = role_choices,max_length=100, null= False, blank= False, default="owner")
	company= models.ForeignKey(Company, on_delete=models.CASCADE, default= None, related_name="company", null=True)
	user=models.ForeignKey(UserProfile, on_delete=models.CASCADE, default= None, null=True, verbose_name="userprofile")
	created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))
	def __unicode__(self): #__str__ for python 3.3
		#return smart_unicode( self.user.user.first_name.title()+ '( %s )' %(self.name.title()))
		return smart_unicode( self.user.user.first_name.title()+' '+self.user.user.last_name.title() )
	class Meta:
		unique_together = (("user", "company"),)

post_save.connect(role_type_post_save, sender = Role, dispatch_uid='post_role_save')


class Transaction(models.Model):
	''' 
	ALL UNITS ARE IN GR, ALTHOUGH THE TRANSACTION UNIT IS SAVED
	'''
	
	weightChoices = (
		('gr', _('Grams')),
		('kg', _('Kilograms')),
		('oz', _('Ounces')),
	)
	tipo_choices = (
		('compra', _('Buy')),
		('venta', _('Sell')),
		('abono', _('Fund')),
	)
	user = models.ForeignKey(User, default= None, null= False)
	from_user = models.ForeignKey(User, default= None, null= True, blank= True, related_name="from_user",help_text=_("Only used when owner funds broker"))
	company= models.ForeignKey(Company, default= None, null = True, on_delete= models.SET_NULL)
	tipo = models.CharField(choices=tipo_choices,max_length=100, null= False, blank= False)
	cantidad = models.DecimalField( null = True, blank = True, decimal_places = 4, max_digits= 50, default= 0)
	precio = models.DecimalField( null = True, blank = True, decimal_places = 2, max_digits= 50, default= 0)
	pesoPost = models.DecimalField( null = True, blank = True, decimal_places = 4, max_digits= 50, default= 0)
	fundido = models.BooleanField(default= False)
	legal = models.BooleanField(default= False)
	weightUnit= models.CharField(choices =weightChoices, max_length=100, null= True, blank= True, default= '')
	evalCost = models.DecimalField( null = True, blank = True, decimal_places = 2, max_digits= 50, default= None)
	meltCost = models.DecimalField( null = True, blank = True, decimal_places = 2, max_digits= 50, default= None)
	balance = models.DecimalField( null = True, decimal_places = 4, max_digits= 50, default= 0)
	created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))
	sell_date = models.DateTimeField(null= True,blank= True)
	buy_date = models.DateTimeField(null= True,blank= True)
	currency = models.CharField(null= True, blank = True, max_length= 10, default='')
	objects = TransactionManager()
	related_transaction = models.ForeignKey('self', null=  True, blank = True, default= None)
	approved = models.NullBooleanField( default = None, verbose_name = _('Approved') )
	last_modified = models.DateTimeField(auto_now= True)
	account = models.ForeignKey('Account',default= None,null = True,blank = True)
	pesoPostLegal = models.DecimalField( null = True, blank = True, decimal_places = 2, max_digits= 50, default= None)
    
    #order descending by date
	class Meta:
		ordering = ['-created']
#pre_save.connect(transaction_pre_save, sender = Transaction, dispatch_uid='pre_transaction_created')
post_save.connect(transaction_post_save, sender = Transaction, dispatch_uid='post_transaction_created')


class Account(models.Model):
	created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))	
	role = models.ForeignKey(Role, default= None, null= False)
	#name = models.CharField(max_length=100, null= False, blank= False)
	start_balance = models.DecimalField( null = False, blank = False, decimal_places = 4, max_digits= 50, default= 0)
	balance = models.DecimalField( null = False, blank = False, decimal_places = 4, max_digits= 50, default= 0)
	account_type=models.ForeignKey('AccountType', default= None)

class AccountType(models.Model):
	#role = models.ForeignKey(Role, default= None, null= False)
	name = models.CharField(max_length=25, null= False, blank= False, unique= True)
	currency_nick = models.CharField( max_length=5, null= False, blank= False, unique= True)
	#balance = m
	def __unicode__(self): #__str__ for python 3.3
		return smart_unicode( self.name)

post_save.connect(acc_type_post_save, sender = AccountType, dispatch_uid='post_account_type_created')


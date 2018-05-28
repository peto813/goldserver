# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import dateutil.parser
#from django.shortcuts import render
from rest_auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.conf import settings
from django.core.mail import send_mail, send_mass_mail#, mail_admins, EmailMessage, EmailMultiAlternatives, get_connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny#, AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturalday
from django.http import Http404
from gold_admin.serializers import *
from gold_admin.filters import *
from gold_admin.permissions	 import *
from gold_admin.utils import *
from django.utils.translation import gettext, gettext_lazy as _
from rest_auth.registration.serializers import RegisterSerializer
from allauth.account.utils import complete_signup
from django.db.models import Q, Sum
from rest_auth.registration.views import RegisterView
from rest_auth.utils import jwt_encode
from rest_auth.app_settings import (TokenSerializer,
                                    JWTSerializer,
                                    create_token)

from allauth.account import app_settings as allauth_settings
from django.contrib.sites.shortcuts import get_current_site
from django.template import loader
from django.utils import timezone# Create your views here.
class SearchUserView(APIView):
	permission_classes = (
		IsAuthenticated,
		IsCompanyOwner
	)
	def post(self, request):
		instance= None
		searchfield= request.data.get('search')
		user_queryset=User.objects.filter(
		    Q(username=searchfield) | Q(email=searchfield) | Q(userprofile__id_number=searchfield)
		)

		if user_queryset.exists() and user_queryset.first().userprofile.basic_role=='broker':
			instance= user_queryset.first()

		if instance:
			serializer=UserSerializer(instance)
			return Response(serializer.data, status = status.HTTP_200_OK )
		else:
			return Response({}, status=status.HTTP_400_BAD_REQUEST)

# class CustomLoginView(LoginView):
#     # def login(self):
#     #     self.user = self.serializer.validated_data['user']
#     #     #find if user is only tied to one company
#     #     companies =self.user.userprofile.companies
#     #     if companies.count()==1:
#     #     	self.request.user.session['company_id'] = companies.first().id
#     #     if getattr(settings, 'REST_USE_JWT', False):
#     #         self.token = jwt_encode(self.user)
#     #     else:
#     #         self.token = create_token(self.token_model, self.user,
#     #                                   self.serializer)

#     #     if getattr(settings, 'REST_SESSION_LOGIN', True):
#     #         self.process_login()

#     # def process_login(self):
#     #     django_login(self.request, self.user)
# 	def set_session_variables(self):
# 		companies =self.user.userprofile.companies
# 		print self.request.user
# 		print companies.count(), type(companies.count())
# 		if companies.count()==1:
# 			self.request.session['company_id'] = companies.first().id
# 			self.request.session.modified = True
# 			print self.request.session.get('company_id')

# 	def post(self, request, *args, **kwargs):
# 		self.request = request
# 		self.serializer = self.get_serializer(data=self.request.data,context={'request': request})
# 		self.serializer.is_valid(raise_exception=True)
# 		self.login()
# 		self.set_session_variables()
# 		return self.get_response()

class AffiliateBroker(APIView):
	permission_classes = (
		IsAuthenticated,
		IsCompanyOwner,
	)

	# def get_queryset(self):
	# 	company = self.request.GET.get('company')
	# 	queryset= self.queryset.filter(userprofile__company= company)
	# 	return [item for item in queryset if item.userprofile.basic_role=='broker']

	"""Affiliates a broker to a given company by creating a role"""
	def post(self, request, pk = None):
		response= {}
		company= Company.objects.filter(pk=pk)
		broker= User.objects.filter(email= request.data.get('email'))
		if company.exists() and broker.exists():
			role, created= Role.objects.get_or_create(name='broker', company= company.first(), user = broker.first().userprofile)
			brokerserializer= UserSerializer(broker.first())
			stat= 'created' if created else 'exists'
			response= {'status':stat, 'broker':brokerserializer.data}
		else:
			return Response('either company or broker do not exist', status=status.HTTP_400_BAD_REQUEST)
		return Response(response, status = status.HTTP_200_OK )
		

class BrokerView(RegisterView):
	"""	this view handles the CRUD aspects for company brokers"""
	queryset = User.objects.all()
	permission_classes = (
		IsAuthenticated,
		IsCompanyOwner,
	)
	serializer_class = BrokerSerializer

	def get_object(self, pk):
		try:
			return User.objects.get(pk=pk)
		except User.DoesNotExist:
			raise Http404

	def get_queryset(self):
		company = self.request.GET.get('company')
		queryset= self.queryset.filter(userprofile__company= company)
		return [item for item in queryset if item.userprofile.basic_role=='broker']

	def get(self, request):
		queryset = self.get_queryset()
		query_params= request.query_params
		if query_params.get('userprofile'):
			# get users with the given id ( should only be one)
			userprofile= UserProfile.objects.filter(id=userprofile)
			if userprofile.exists():
				queryset = userprofile
		serializer = UserSerializer(queryset, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK )


	def delete(self, request):
		query_params= request.query_params
		company= query_params.get('company')
		userprofile	=query_params.get('userprofile')
		role = Role.objects.get(company=company, user= userprofile)
		role.delete()
		return Response(role.user.pk, status = status.HTTP_200_OK )

	def create(self, request, *args, **kwargs):
		data= request.data.copy()
		data['company'] = request.query_params.get('company')
		serializer = BrokerSerializer(data=data)
		serializer.is_valid(raise_exception=True)
		user = self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)
		user_serializer = UserSerializer(user)
		return Response(user_serializer.data,status=status.HTTP_201_CREATED, headers=headers)

class TransactionsView(APIView):
	'''
	This view handles CRUD aspect of gold transactions
	'''
	queryset = Transaction.objects.all()
	permission_classes = (IsAuthenticated,  UserIsRelatedToCompany,)
	serializer_class = TransactionSerializer


	def get_object(self, pk):
		try:
			return Transaction.objects.get(pk=pk)
		except Transaction.DoesNotExist:
			raise Http404

	def get_queryset(self, company_id):
		'''
		make sure transactions are all that belong to company for owner
		and only for broker when broker
		'''
		basic_role= self.request.user.userprofile.basic_role
		queryset= self.queryset.filter(company= company_id )
		print queryset
		if queryset.exists():
			#make sure user is asocciated with company and is authenticated
			company= queryset.first().company
			self.check_object_permissions(self.request, company)

		if basic_role=='broker':
			queryset = self.queryset.filter(user = self.request.user)

		#print queryset, company_id,194
		#print '180738917'
		now = timezone.now()
		min_date = now.replace(hour= 0, minute = 0, second=0,microsecond=0)
		max_date = now.replace(hour= 23, minute = 59, second=59, microsecond=999999)
		#print min_date, max_date
		#print queryset.filter(created__range=(min_date, max_date)), 199
		return queryset.filter(created__range=(min_date, max_date))

	def user_pending_transactions(self):
		return self.queryset.filter(user=self.request.user,tipo='abono', approved=None)

	def broker_has_pending_transactions(self):
		#print transactions.values()
		has_pending_transactions= False
		user= self.request.user
		user_is_broker= user.userprofile.basic_role == 'broker'
		user_has_pending_transactions = self.user_pending_transactions().exists()
		#print user_has_pending_transactions
		#print user_has_pending_transactions, user_is_broker, 207
		return user_is_broker and user_has_pending_transactions

	def get_message(self, transactions):
		#for every pending transaction should build a string that lists the approval dates needed.
		dates_list=[]
		user_is_broker= self.request.user.userprofile.basic_role == 'broker'
		if user_is_broker:
			#user_pending_transactions = self.user_pending_transactions()
			for transaction in self.user_pending_transactions():
				date_string= naturalday(transaction.created)
				dates_list.append(date_string)
			transaction_dates=list_to_string(dates_list, ' | ')
			message= _('You have pending transactions for %s' %(transaction_dates))
		return message


	def get_accounts(self, companyId):
		user = self.request.user
		role = user.userprofile.role_set.filter(user = user.userprofile, company= companyId)
		if role.exists():
			role= role.first()
			serializer = AccountSerializer(role.account_set.filter(role=role), many= True)
			return serializer.data
		return None

	def get(self, request, companyId= None):
		context	={}
		queryset = self.get_queryset(companyId)
		serializer= self.serializer_class(queryset, many= True)
		context['data']= serializer.data
		message=self.get_message(queryset) if self.broker_has_pending_transactions() else ''
		context=self.add_to_data(context, 'data', serializer.data)
		context=self.add_to_data(context, 'message', message)
		accounts = self.get_accounts(companyId)
		context=self.add_to_data(context, 'accounts', accounts)
		#print context['data']
		return Response(context, status = status.HTTP_200_OK )


	def patch(self,request, company_id= None,pk= None):
		transaction = self.get_object(pk)
		serializer= self.serializer_class(transaction, data=request.data,context = {'request': request}, partial = True)
		serializer.is_valid(raise_exception=True)
		serializer.save(user= request.user)
		return Response(serializer.data, status=status.HTTP_200_OK)


	def get_company(self, pk):
		try:
			return Company.objects.get(pk=pk)
		except Company.DoesNotExist:
			raise Http404

	def add_to_data(self, data,key, value):
		new_data= data.copy()
		new_data[key] = value
		return new_data

	def get_context(self, company):
		context= {
			'data':self.serializer.data,
			'accounts': self.get_accounts(company)
		}
		return context

	def post(self, request, pk= None):
		company= self.get_company(pk)
		data=self.add_to_data(request.data, 'company', pk)
		self.check_object_permissions(request, company)
		serializer= self.serializer_class(data = data, context = {'request': request})
		if serializer.is_valid():
			params = {'user' : request.user} if (serializer.validated_data.get('tipo') !='abono') else {}
			instance = serializer.save(**params)
			queryset= self.get_queryset(pk)
			self.serializer= self.serializer_class(queryset,many= True)
			return Response(self.get_context(pk), status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		#serializer.is_valid(raise_exception=True)

		


class SearchTransactionDatesView(APIView):
	queryset = Transaction.objects.all()
	permission_classes = (IsAuthenticated,UserIsRelatedToCompany,)
	serializer_class = TransactionSerializer

	def get_queryset(self, company):
		'''
		make sure transactions are all that belong to company for owner
		and only for broker when broker
		'''
		queryset, self.mindate, self.maxdate = Transaction.objects.query_date(self.request)
		basic_role= self.request.user.userprofile.basic_role
		queryset= queryset.filter(company= company )
		if queryset.exists():
			company= queryset.first().company
			self.check_object_permissions(self.request, company)

		if basic_role=='broker':
			queryset = self.queryset.filter(user = self.request.user)

		return queryset

	def get_context(self,serializer):
		context= {
			'range':{
				'mindate':self.mindate,
				'maxdate':self.maxdate
			},
			'transactions':serializer.data
		}
		return context

	def post(self, request, company= None):
		queryset = self.get_queryset(company)
		serializer = self.serializer_class(queryset, many= True)
		context= self.get_context(serializer)
		return Response(context, status = status.HTTP_200_OK )


class ApproveFundsView(TransactionsView):
	'''
	this view finds a username and delivers error if not found
	'''
	queryset = Transaction.objects.all()
	permission_classes = (IsAuthenticated,  IsCompanyBroker,IsOwner,)
	serializer_class = TransactionSerializer

	def get_class_name(self):
		return self.__class__.__name__

	def get_object(self, pk):
		try:
			return Transaction.objects.get(pk=pk)
		except Transaction.DoesNotExist:
			raise Http404


	def get_context(self, company):
		context= {
			'data':self.serializer.data,
			'accounts': self.get_accounts(company)
		}
		return context

	def get(self, request, pk= None):
		transaction= self.get_object(pk)
		self.check_object_permissions(request, transaction)
		if transaction and transaction.tipo=='abono':
			transaction.approved=True
			transaction.account.balance+=transaction.precio
			transaction.account.save()
			transaction.save()
			self.notify_parts(transaction)
			#get balance
			# self.notify_parts(transaction)
			self.serializer= self.serializer_class(transaction)
			return Response(self.get_context(pk), status=status.HTTP_200_OK)
		return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST)


	def get_messages(self, transaction):
		'''
		the code below is dedicated for construnction of the brokers notificacion
		need to implement for all company brokers as well
		'''
		messages=[]
		current_site = get_current_site(self.request)
		accept_status = _('accepted') if (self.get_class_name() =='ApproveFundsView' ) else _('rejected')

		#full_name = None # full name of a particular owner
		
		broker = self.request.user.first_name.title() +' ' +self.request.user.last_name.title()
		currency = transaction.account.account_type.currency_nick
		amount = transaction.precio
		subject_context={
			'accept_status': accept_status
		}

		subject = loader.render_to_string('account/email/broker_accepted_funds_subject.txt', subject_context)
		
		message_context={
			'full_name': broker,
			#'broker': broker,
			'accept_status' : accept_status,
			'currency':currency.title(),
			'amount': amount,
			'current_site': current_site
		}
		message = loader.render_to_string('account/email/broker_accepted_funds_message.txt', message_context)
		broker_message =(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.user.email])

		messages.append(broker_message)






		#build owner messages
		owner_roles = Role.objects.filter(company = transaction.company, name="owner")

		#owner_messages= []
		owner_subject = loader.render_to_string('account/email/owner_accepted_funds_subject.txt', subject_context)

		for owner in owner_roles:
			message_context={
				'full_name': owner,
				'broker': broker,
				'accept_status' : accept_status,
				'currency':currency,
				'amount': amount,
				'current_site': current_site
			}
			message = loader.render_to_string('account/email/owner_accepted_funds_message.txt', message_context)

			owner_message=(owner_subject, message, settings.DEFAULT_FROM_EMAIL, [owner.user.user.email])
			messages.append(owner_message)
		return tuple(messages)



	def notify_parts(self,transaction):
		#message_list=[]
		messages= self.get_messages(transaction)
		#owner_messages= self.get_owner_messages(transaction)
		# message_list=[item for item in owner_messages]
		# message_list.append(broker_message)
		#mail_tuple= tuple(messages)
		send_mass_mail(messages, fail_silently=False)


class RejectFundsView(ApproveFundsView):
	'''
	this view finds a username and delivers error if not found
	'''
	# queryset = Transaction.objects.all()
	# permission_classes = (IsAuthenticated,  IsCompanyBroker)
	# serializer_class = TransactionSerializer

	# def get_object(self, pk):
	# 	try:
	# 		return Transaction.objects.get(pk=pk)
	# 	except Transaction.DoesNotExist:
	# 		raise Http404

	def get(self, request, pk= None):
		transaction= self.get_object(pk)
		self.check_object_permissions(request, transaction)
		if transaction:
			transaction.approved=False
			transaction.save()
			self.notify_parts(transaction)
			self.serializer= self.serializer_class(transaction)
			return Response(self.get_context(pk), status = status.HTTP_200_OK )
		return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST)



class VerifyUserView(APIView):
	'''
	this view finds a username and delivers error if not found
	'''
	queryset = User.objects.all()
	permission_classes = (IsAuthenticated,  IsCompanyOwner,)
	serializer_class = TransactionSerializer
	def get(self, request, pk= None):
		user= User.objects.filter(username=pk)
		if user.exists():
			serializer= UserSerializer(user.first())
			return Response(serializer.data, status = status.HTTP_200_OK )
		return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
	'''
	this view finds a username and delivers error if not found
	'''
	queryset = User.objects.all()
	permission_classes = (IsAuthenticated,  IsCompanyOwner,)
	serializer_class = TransactionSerializer
	def post(self, request):
		email=  request.data['email']
		user= User.objects.filter(email=email)
		if user.exists():
			serializer= UserSerializer(user.first())
			return Response(serializer.data, status = status.HTTP_200_OK )
		return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST)


class VerifyCedula(APIView):
	'''
	this view finds a username and delivers error if not found
	'''
	queryset = User.objects.all()
	permission_classes = (IsAuthenticated,  IsCompanyOwner,)
	serializer_class = TransactionSerializer
	def get(self, request, pk= None):
		user= User.objects.filter(userprofile__id_number=pk)
		if user.exists():
			serializer= UserSerializer(user.first())
			return Response(serializer.data, status = status.HTTP_200_OK )
		return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST)

class WalletView(APIView):
	'''
	This view handles CRUD aspect of Wallets
	'''
	queryset = Account.objects.all()
	permission_classes = (IsAuthenticated,  IsCompanyOwner,)
	serializer_class = AccountSerializer

	def get_object(self, pk):
		try:
			return Account.objects.get(pk=pk)
		except Account.DoesNotExist:
			raise Http404

	# def get_queryset(self):
	# 	return self.queryset.filter(user = self.request.user)

	def patch(self,request, pk= None):
		account = self.get_object(pk)
		serializer= self.serializer_class(account, data=request.data,context = {'request': request}, partial = True)
		serializer.is_valid(raise_exception=True)
		serializer.save(user= request.user)
		serializer= UserSerializer(account.role.user.user)
		return Response(serializer.data, status=status.HTTP_200_OK)

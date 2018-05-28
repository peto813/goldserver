# -*- coding: utf-8 -*-
import decimal
from rest_framework import serializers
from rest_auth.serializers import UserDetailsSerializer,TokenSerializer
from gold_admin.models import *
from rest_auth.models import TokenModel
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from rest_auth.serializers import LoginSerializer, PasswordResetSerializer,PasswordChangeSerializer
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext, gettext_lazy as _
from django.core.mail import send_mail
from rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import User
from django.template import loader
from django.contrib.humanize.templatetags.humanize import intcomma
from allauth.account.adapter import get_adapter
try:
    from allauth.account import app_settings as allauth_settings
    from allauth.account.utils import setup_user_email
    from allauth.utils import (email_address_exists,
                               get_username_max_length)
except ImportError:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'





class CountrySerializer(serializers.ModelSerializer):
	class Meta:
		model = Country
		fields = '__all__'


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    account_type=AccountTypeSerializer()
    class Meta:
        model = Account
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.balance+=validated_data.get('balance')
        instance.save()
        self.send_email_broker(instance.role.user.user)
        return instance

    def send_email_broker(self, broker):
        # send_mail(
        #     'Subject here',
        #     'Ha recibido la cantidad de %s',
        #     'from@example.com',
        #     ['to@example.com'],
        #     fail_silently=False,
        # )
        pass

class RoleSerializer(serializers.ModelSerializer):
    accounts= serializers.SerializerMethodField(read_only = True)

    #role = serializers.SerializerMethodField(read_only = True)

    def get_accounts(self, role):
        accounts=role.account_set.all()
        serializer= AccountSerializer(accounts, many= True)
        return serializer.data


    class Meta:
        model = Role
        fields = '__all__'


class CustomUserSerializer(serializers.ModelSerializer):

    # location = serializers.CharField(required = False)
    companies= CompanySerializer(many = True, read_only= True)
    #roles= RoleSerializer(read_only= True)
    roles = RoleSerializer(many= True, read_only= True)
    # id_number= serializers.CharField( required = True)
    # picture= serializers.CharField(required= False)
    # mobile=serializers.CharField(required= False)
    # other=serializers.CharField(required= False)
    # office=serializers.CharField( required = False)
    class Meta:
        model = UserProfile
        #fields = ('location','company', 'role', 'id_number', 'picture', 'mobile', 'other', 'office',)
        fields = '__all__'

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        instance = super(CustomUserSerializer, self).update(instance, validated_data)

        # get and update user profile
        profile = instance.userprofile
        if profile_data:
            profile.location = profile_data.get('location', None)
            profile.company = profile_data.get('company', None)
            profile.role = profile_data.get('role', None)
            profile.id_number = profile_data.get('id_number', None)
            profile.picture = profile_data.get('picture', None)
            profile.mobile = profile_data.get('mobile', None)
            profile.other = profile_data.get('other', None)
            profile.office = profile_data.get('office', None)
            profile.save()
        return instance


# class customPasswordResetSerializer(PasswordResetSerializer):
#     password_reset_form_class = customPasswordResetForm
#     def validate_email(self, value):
#         # Create PasswordResetForm with the serializer
#         self.reset_form = self.password_reset_form_class(data=self.initial_data)
#         try:
#             email = User.objects.get(email = value)
#         except:
#             raise serializers.ValidationError(_("E-mail does not exist"))
#         if not self.reset_form.is_valid():
#             raise serializers.ValidationError(self.reset_form.errors)
#         return value


class UserSerializer(UserDetailsSerializer):
    userprofile =CustomUserSerializer(read_only= True)
    role = serializers.SerializerMethodField(read_only = True)

    def get_role(self, user):
        return 'admin' if user.is_superuser else user.userprofile.basic_role
        # users_company_roles = user.userprofile.company.through.objects.filter(name ='owner')
        # user_has_owner_role =users_company_roles.exists()
        # return 'admin' if user.is_superuser else ('owner' if user_has_owner_role==True else 'broker')

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('userprofile','role',)

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomTokenSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # account_types= serializers.SerializerMethodField(read_only= True)

    # def get_account_types(self, token):
    #     account_types= AccountType.objects.all()
    #     account_types =[{'name': item.name, 'currency_nick': item.currency_nick, 'id': item.pk} for item in account_types]
    #     return account_types

    class Meta:
        model = TokenModel
        fields = ('key', 'user',)



class BrokerSerializer(RegisterSerializer):
    first_name = serializers.CharField(required= True, max_length = 100)
    last_name = serializers.CharField(required= True, max_length = 100)
    company = serializers.PrimaryKeyRelatedField(queryset = Company.objects.all(), required= True)
    id_number = serializers.CharField(required= True, max_length= 100)
    mobile= serializers.CharField( required= False, max_length= 100, allow_blank =True)
    office= serializers.CharField( required= False, max_length= 100, allow_blank =True)
    other= serializers.CharField( required= False, max_length= 100, allow_blank =True)
    location= serializers.CharField(required= True, max_length=250)
    gold_balance = serializers.DecimalField(max_digits= 50, decimal_places= 4, min_value=0)

    def validate_username(self, username):
        username = get_adapter().clean_username(username)
        return username

    def validate_email(self, email):
        email = get_adapter().clean_email(email)

        '''
        get role, raise exception if email exists and pertains to an owner
        '''
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                #get the role of existing email address
                user= User.objects.get(email=email)
                role = user.userprofile.basic_role
                if role=='owner':
                    raise serializers.ValidationError(
                        _("An owner is already registered with this e-mail address."))
        return email


    def custom_signup(self, request, user):
        '''
        we create the new brokers user profile
        '''

        '''
        need to create a role and add it to company relationshiop
        '''
        
        
        data={
            'user': user,
            #'company': company,
            'location': self.validated_data.get('location', None),
            'id_number': self.validated_data.get('id_number', None),
            'mobile': self.validated_data.get('mobile', None),
            'office': self.validated_data.get('office', None),
            'other': self.validated_data.get('other', None),
            'gold_balance': self.validated_data.get('gold_balance', None)
        }
        userprofile= UserProfile.objects.create(**data)
        user.userprofile = userprofile
        user.first_name=self.validated_data.get('first_name', None)
        user.last_name=self.validated_data.get('last_name', None)
        user.save()
        company=self.validated_data.get('company', None)
        role=Role.objects.create(name="broker", company=company, user = userprofile)
        return user

    def save(self, request):
        '''
        we attempt to get the user, if an exception is thrown we create the broker
        '''
        try:
            cleaned_data= self.get_cleaned_data()
            return User.objects.get(email=cleaned_data.get('email'), username=cleaned_data.get('username'))
        except:
            adapter = get_adapter()
            user = adapter.new_user(request)
            self.cleaned_data = self.get_cleaned_data()
            adapter.save_user(request, user, self)
            user = self.custom_signup(request, user)
            setup_user_email(request, user, [])
        return user


class AccountField(serializers.Field):
    def to_representation(self, obj):
        serializer = AccountSerializer(obj)
        return serializer.data

    def to_internal_value(self, data):
        print data
        if data:
            return Account.objects.get( id = data['id'] )
        return None

class TransactionSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    related_transaction = serializers.PrimaryKeyRelatedField(queryset=Transaction.objects.all(), required= False)
    can_be_sold= serializers.SerializerMethodField( read_only = True )
    user_data= serializers.SerializerMethodField( read_only  =True )
    balance= serializers.DecimalField(max_digits= 50, decimal_places= 4, min_value=0, read_only  =True )
    from_user= UserSerializer(read_only= True)
    user= UserSerializer(read_only= True)
    account=AccountField()

    class Meta:
        model = Transaction
        fields = '__all__'

    def get_user_data(self, transaction):
        user_data={
            'full_name': transaction.user.first_name.title() + ' ' +transaction.user.last_name.title()
        }
        return user_data

    def get_can_be_sold(self, transaction):
        can_be_sold = True
        is_sale=transaction.tipo =='venta'
        has_related_transaction = hasattr(transaction, 'related_transaction') and transaction.related_transaction is not None
        transaction_is_sale = True if (has_related_transaction and transaction.related_transaction.tipo=='venta') else False
        has_related_sale = True if (has_related_transaction and transaction_is_sale) else False
        if (transaction.tipo=='compra' and has_related_sale) or is_sale or transaction.tipo=='abono':
            can_be_sold = False
        return can_be_sold

    def get_total(self, validated_data):
        precio = validated_data.get('precio', decimal.Decimal(0))
        precio_fundicion = validated_data.get('meltCost', decimal.Decimal(0))
        precio_legalizacion = validated_data.get('evalCost', decimal.Decimal(0))
        total = precio + precio_fundicion + precio_legalizacion
        return total

    def validate(self, validated_data):
        fundido = validated_data.get('fundido', None)
        meltCost = validated_data.get('meltCost', None)
        legal = validated_data.get('legal', None)
        evalCost = validated_data.get('evalCost', None)
        pesoPost = validated_data.get('pesoPost', None)
        tipo = validated_data.get('tipo')
        cantidad = validated_data.get('cantidad', None)
        weightUnit = validated_data.get('weightUnit', None)
        currency = validated_data.get('currency', None)
        account = validated_data.get('account', None)
        precio = validated_data.get('precio', None)



        if tipo !='abono':
            if tipo =='compra' and (account.balance < self.get_total(validated_data)):
                raise serializers.ValidationError(_('Insufficient funds.'))
            if not cantidad:
                raise serializers.ValidationError(_('Missing amount.'))


        if fundido and not (meltCost or pesoPost):
            raise ValidationError(_('Melt cost and remaining amount are required.'))
        if legal and not evalCost:
            raise ValidationError(_('Evaluation cost is required.'))

        return validated_data

    def send_broker_notification(self, transaction):
        request= self.context['request']
        current_site = get_current_site(request)

        message_context={
            'full_name':  transaction.user.first_name.title()+' '+transaction.user.last_name.title(),
            'funder' : transaction.from_user.first_name.title()+' '+transaction.from_user.last_name.title(),
            'company_name':transaction.company.name.title(),
            'currency': transaction.account.account_type.currency_nick.title(),
            'amount': intcomma(transaction.precio),
            'current_site':current_site
        }
        subject = loader.render_to_string('account/email/notify_broker_funded_subject.txt')
        message = loader.render_to_string('account/email/notify_broker_funded_message.txt', message_context)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.user.email])

    def create_fund_transaction(self,validated_data):
        '''
        method that handles transactions where the owner funds the brokers wallet
        and broker is notified via email
        '''
        request=self.context['request']
        validated_data['from_user'] = request.user
        transaction = Transaction.objects.create(**validated_data)
        self.send_broker_notification(transaction)


    def create_regular_transaction(self, validated_data):
        tipo = validated_data.get('tipo')
        request= self.context['request']
        user = request.user
        user_gold_balance = decimal.Decimal(user.userprofile.gold_balance)
        #validated_data['cantidad'] = validated_data.get('cantidad')#, validated_data.get('weightUnit')
        cantidad= validated_data.get('cantidad')
        #validated_data['pesoPost'] =validated_data.get('pesoPost')#, validated_data.get('weightUnit')
        pesoPost=validated_data.get('pesoPost') 
        validated_data['related_transaction']= validated_data.get('related_transaction') if tipo=='venta' else None
        # mult = decimal.Decimal(((1 if tipo=='compra' else -1)))
        # new_bal = user_gold_balance+( mult*(decimal.Decimal(pesoPost) if pesoPost else cantidad) )
        # user.userprofile.gold_balance = new_bal
        # user.userprofile.save()
        #validated_data['balance'] =new_bal
        #request.user.userprofile.save()
        transaction = Transaction.objects.create(**validated_data)
        return transaction

    def create(self, validated_data):
        tipo = validated_data.get('tipo')
        transaction = self.create_fund_transaction() if tipo =='abono' else self.create_regular_transaction(validated_data)
        return transaction


    def update(self, instance, validated_data):
        instance.legal = validated_data.get('legal', instance.legal)
        instance.fundido = validated_data.get('fundido', instance.fundido)
        instance.pesoPost = validated_data.get('pesoPost', instance.pesoPost)
        instance.meltCost = validated_data.get('meltCost', instance.meltCost)
        instance.evalCost = validated_data.get('evalCost', instance.evalCost)
        instance.save()
        return instance



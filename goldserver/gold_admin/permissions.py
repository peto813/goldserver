# -*- coding: utf-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS
from gold_admin.models import Role
# from django.contrib.auth import logout
# from django.contrib.auth.models import User
# from rest_framework.exceptions import APIException
# from rest_framework import status
# from utils import get_user_type
# from condominioaldia_app.models import Inmueble
# from django.utils.translation import gettext, gettext_lazy as _
class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsCompanyOwner(BasePermission):

    # def has_object_permission(self, request, view, obj):
    #     print 1
    #     return obj.cerrado==False or (request.method in SAFE_METHODS)

    def has_permission(self, request, view):
        owner_roles= request.user.userprofile.roles.filter(name='owner')
        return owner_roles.exists() 

class IsCompanyBroker(BasePermission):

    # def has_object_permission(self, request, view, obj):
    #     print 1
    #     return obj.cerrado==False or (request.method in SAFE_METHODS)

    def has_permission(self, request, view):
        broker_roles= request.user.userprofile.roles.filter(name='broker')
        return broker_roles.exists() 




class UserIsRelatedToCompany(BasePermission):

    # def has_object_permission(self, request, view, obj):
    #     print 1
    #     return obj.cerrado==False or (request.method in SAFE_METHODS)

    # def has_permission(self, request, view):
    #     #company= request.data.get('companyId')
    #     #print request.query_params, 'quer params'
    #     print view.kwargs, 'pppppppppppppppp'
    #     print view.kwargs.get('companyId', None), 'asdasdasda'
    #     print view.kwargs.get('pk', None), 'bbbbbbbbbbbbb'
    #     #print company, 'teta'
    #     roles =Role.objects.filter(user=request.user, company= company)
    #     #print roles, 'roles'
    #     user_roles= request.user.userprofile.roles.filter(user=request.user.userprofile, company=company)
    #     #print user_roles
    #     return user_roles.exists() 


    def has_object_permission(self, request, view, company):
        #is the user associated with the company
        role= Role.objects.filter(company= company,user =request.user.userprofile)
        
        return role.exists()
        #return True

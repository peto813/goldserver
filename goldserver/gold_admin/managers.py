# -*- coding: utf-8 -*-
import datetime
from django.db import models
from datetime import timedelta
import pytz
from django.utils import timezone

class TransactionManager(models.Manager):
    '''
    returns a tuple with the queryset begin date and end date
    '''
    def query_date(self, request):
        data = request.data
        rangeParam= data.get('tipo')
        endDate = timezone.now()
    	if rangeParam=='mes':
    		startDate = endDate - timedelta( days=30 )
    		#endDate=datetime.today()
    	elif rangeParam=='semana':
    		startDate = endDate - timedelta( days=7 )
    		#endDate=datetime.today()
    	elif rangeParam=='dia':
    		startDate = endDate
        elif rangeParam=='custom':
            startDate = data.get('fromDate', None)
            endDate = data.get('toDate', None)
            startDate=datetime.datetime(startDate['year'], startDate['month'], startDate['day'], 0,0, tzinfo=pytz.utc)
            endDate=datetime.datetime(endDate['year'], endDate['month'], endDate['day'], 0,0, tzinfo=pytz.utc)

        startDate = startDate.replace(hour= 0, minute = 0, second=0,microsecond=0)
        endDate = endDate.replace(hour= 23, minute = 59, second=59, microsecond=999999 )
    	queryset = self.filter(created__range=(startDate, endDate))
        return (queryset, startDate,endDate,)

    # def get_debtors(self, condominio):
    #     return self.filter(condominio = condominio).filter(deuda_actual__lt = 0)

    # def get_creditors(self, condominio):
    #     return self.filter(condominio = condominio).filter(deuda_actual__gte = 0)

    # def get_board_members(self, condominio):
    #     return self.filter(condominio = condominio).filter(junta_de_condominio = True)

    # def get_non_board_members(self, condominio):
    #     return self.filter(condominio = condominio).filter(junta_de_condominio = False)

    # def get_particular_property(self, condominio, inmueble):
    #     return self.filter(condominio = condominio).filter(pk = inmueble)      
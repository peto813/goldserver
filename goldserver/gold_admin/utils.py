
import decimal, calendar, pytz, datetime, requests
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

def massToGrams(mass, fromUnit=None):
    if mass and fromUnit:
        mass=decimal.Decimal(mass)
        conversionFactor={
            'kg': decimal.Decimal(1/1000),
            'oz':decimal.Decimal(28.3495),
            'gr':decimal.Decimal(1)
        }
        if fromUnit=='gr':
            return mass
        return mass * conversionFactor[fromUnit]
    return None


def last_day_of_month(date):
	lastdayofmonth = calendar.monthrange( date.year,  date.month )[1]
	return lastdayofmonth

def list_to_string( myList, separator=None ):
    return (('%s')%(separator)).join(map(str, myList)) 




def get_aware_datetime(date_str):
    ret = parse_datetime(date_str)
    if not is_aware(ret):
        ret = make_aware(ret)
    return ret
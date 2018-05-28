"""goldserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from gold_admin import views

#from rest_auth.views import LoginView, PasswordResetView, PasswordChangeView

# router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = [
    #url(r'^rest-auth/password/reset/$', views.customPasswordResetView.as_view(), name='rest_password_reset'),
	#url(r'^rest-auth/login/$', views.CustomLoginView.as_view(), name='rest_login'),
    url(r'^rest-auth/', include('rest_auth.urls')),
	url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
	url(r'^accounts/', include('allauth.urls')),
	url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^admin/', admin.site.urls),

    # transactions urls
    #url(r'^api/transactions/$', views.TransactionsView.as_view(), name="transactions"),
    url(r'^api/transactions/(.*?)/$', views.TransactionsView.as_view(), name="transactions"),
    url(r'^api/querytransactiondates/(.*?)/$', views.SearchTransactionDatesView.as_view(), name="querytransactiondates"),


    #fund approvals
    url(r'^api/approvefunds/(.*?)/$', views.ApproveFundsView.as_view(), name='approvefunds'),
    url(r'^api/rejectfunds/(.*?)/$', views.RejectFundsView.as_view(), name='rejectfunds'),
    
    #verification urls
    url(r'^api/verifyuser/(.*?)/$', views.VerifyUserView.as_view(), name='verifyuser'),
    url(r'^api/verifyemail/$', views.VerifyEmailView.as_view(), name='verifyemail'),
    url(r'^api/verifycedula/(.*?)/$', views.VerifyCedula.as_view(), name='verifycedula'),

    url(r'^api/broker/$', views.BrokerView.as_view(), name='broker'),
    url(r'^api/broker/(?P<company>[0-9]+)/(?P<userprofile>[0-9]+)$', views.BrokerView.as_view(), name='broker'),
    url(r'^api/wallet/(.*?)/$', views.WalletView.as_view(), name='wallet'),
    url(r'^api/affiliatebroker/(.*?)/$', views.AffiliateBroker.as_view(), name='affiliatebroker'),
    url(r'^api/searchuser/', views.SearchUserView.as_view(), name='searchuser'),
    url(r'^accounts/', include('django.contrib.auth.urls')),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
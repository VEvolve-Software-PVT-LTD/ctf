from django.conf.urls import url
from django.urls import  path
from channels.auth import AuthMiddlewareStack
from ctf import consumers


#websocket_urlpatterns = [
#    url(
#        'ws/customer-service/(?P<pk>[0-9]+)/', 
#        consumers.ChatConsumer
#    )
#    
#]
#
#http_urlpatterns = [
#    path(
#        "customer-service/notify/",
#        AuthMiddlewareStack(
#            consumers.ChatNotifyConsumer
#        )
#    )
#]


from django.conf.urls import url
from channels.routing import URLRouter
from channels.http import AsgiHandler
from channels.auth import AuthMiddlewareStack
import django_eventstream

urlpatterns = [
	url(r'^events/', AuthMiddlewareStack(
		URLRouter(django_eventstream.routing.urlpatterns)
	), {'channels': ['time']}),
	url(r'', AsgiHandler),
]
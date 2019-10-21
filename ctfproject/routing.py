#from django.urls import re_path
#from channels.auth import AuthMiddlewareStack
#from channels.routing import ProtocolTypeRouter, URLRouter
#from channels.http import AsgiHandler
#import ctf.routing
#application = ProtocolTypeRouter(
#    {
#        "websocket": AuthMiddlewareStack(
#            URLRouter(ctf.routing.websocket_urlpatterns)
#        ),
#        "http": URLRouter(
#            ctf.routing.http_urlpatterns
#            + [re_path(r"", AsgiHandler)]
#        ),
#    }
#)

#from channels.routing import ProtocolTypeRouter, URLRouter
#import ctf.routing

#application = ProtocolTypeRouter({
#	'http': URLRouter(ctf.routing.urlpatterns),
#})

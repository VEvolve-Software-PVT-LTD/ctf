from django.conf.urls import url,include
from django.contrib import admin

from django.conf.urls import (
handler400, handler403, handler404, handler500
)

handler404 = 'ctf.views.handler404'
handler500 = 'ctf.views.handler500'


urlpatterns = [

    url(r'^admin/', admin.site.urls),    
    url(r'^', include('ctf.urls'))
]

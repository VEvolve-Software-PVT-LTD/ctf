from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from ctf import views

urlpatterns = [
    
    
    url(r'^questions/(?P<pk>[0-9]+)/detail/$', views.get_question_detail, name='question_detail'),
    url(r'^questions/(?P<pk>[0-9]+)/clue/$', views.get_clue, name='question_clue'),
    url(r'^team_dashboard/(?P<pk>[0-9]+)/profile$', views.TeamDashBoard.as_view(), name='team_dash_board'),
    url(r'^answer_question/$',views.answer_question, name='answer_question'),
    url(r'^questions/$', views.get_questions_list, name='questions_list'),
    url(r'^team_rankings/$', views.team_rankings, name='team_rankings'),
    url(r'^permission_denied/$', views.permission_denied, name='permission_denied'),
    url(r'^customer-service/(?P<pk>[0-9]+)/$', views.room, name='cs_chat'),
    url(r'^customer-service/', TemplateView.as_view(template_name='customer_service.html'), name='cs_main'),
    url(
        r'^login/$', 
        auth_views.LoginView.as_view(), 
        {'template_name': 'login.html'}, 
        name='login_view'
    
        ),
    
    url(
        r'^logout/$', 
        auth_views.LogoutView.as_view(), 
        name='logout_view',
        ),
    url(
        r'^register/$',
        views.team_register,
        name='team_register_view'
    ),
    url(r'^$', views.landing_page, name='landing_page'),
    
]
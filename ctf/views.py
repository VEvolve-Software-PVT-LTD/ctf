"""
Author: Balaraju M.
"""
import time
import threading
import json
import redis
from datetime import datetime, timezone
from django.shortcuts import render,redirect,reverse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.views.generic import DetailView
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseServerError,
    HttpResponseRedirect,
)
from django.views.generic import FormView
from django_redis import get_redis_connection
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Sum
# from django_eventstream import get_current_event_id, send_event
# from django_eventstream.channelmanager import DefaultChannelManager
# import datetime
#from kafka import KafkaConsumer
#from kafka import KafkaProducer
from ctf import models
from ctf.forms import AnswerForm,TeamCreateForm,MemberForm

import os.path
from django.conf import settings

# django redis connection.
redis_connection = get_redis_connection("default")

# raw redis connection.
r = redis.Redis()

# kafka producer
#producer = KafkaProducer(bootstrap_servers='localhost:9092')

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


def user_check(user):
    """ check user is team or admin."""
    return hasattr(user, 'team')


def super_user_check(user):
    return user.is_superuser


def permission_denied(request):
    return render(request, 'pd.html')


def handler404(request, *args, **argv):
    response = render(request, '404.html', {})
    response.status_code = 404
    return response


def handler500(request, *args, **argv):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response


def room(request, pk):
    team_id = request.user.team.id
    return render(
        request,
        "help_chat_room.html",
        {"room_name_json": str(team_id)}
    )

def landing_page(request):
    """
    Landing page view caching 6 hours.
    To increase Cache time change the 360.
    """
    return render(request, 'landing_page.html')


@login_required(login_url=reverse_lazy('login_view'))
@user_passes_test(super_user_check,
                  login_url=reverse_lazy('permission_denied'))
def get_teams(request):
    """
    returns total teams.
    teams are fetching with select_related method
    cache into redis.
    """
    team_cache = getattr(settings, TEAM_CACHE)
    if team_cache in cache:
        teams = cache.get(team_cache)
    else:
        teams = list(models.Team.objects.select_related())
        cache.set(team_cache, teams, timeout=CACHE_TTL)
    return render(request, 'teams.html', {'teams': teams})


@login_required(login_url=reverse_lazy('login_view'))
@user_passes_test(user_check,
                  login_url=reverse_lazy('permission_denied'))
def get_questions_list(request):
    """ returns questions list."""
    key = 'vev/1278/ctf-questions'
    user_key = '{}-key'.format(str(request.user.team))
    # print(user_key)
    current_action = "Standing in Questions List"
    r.set(user_key, current_action)
    if key in cache:
        questions = cache.get(key)
    else:
        questions = list(models.Question.objects.all())
        cache.set(key, questions, timeout=CACHE_TTL)

    # print(type(questions))
    team_open_questions = list(models.TeamQuestion.objects.filter(team=request.user.team))
    # print(team_open_questions)
    top_ids = []
    total_qids = []
    tops = []

    for i in questions:
        total_qids.append(i.id)
    # print(total_qids)

    for i in team_open_questions:
        top_ids.append(i.question.id)
    # print(top_ids)
    question_bank = []
    instance_question = {}

    for i in total_qids:
        if i in top_ids:
            question = models.TeamQuestion.objects.get(question__id=i, team=request.user.team)
            instance_question['id']=i
            instance_question['status'] = question.is_completed
            instance_question['points'] = question.base_points
            question_bank.append(instance_question)
            instance_question = {}
        else:
            question = models.Question.objects.get(id=i)
            instance_question['id'] = i
            instance_question['status'] = 'unopen'
            instance_question['points'] = question.question_points
            question_bank.append(instance_question)
            instance_question = {}

        sorted_qb = sorted(question_bank, key = lambda i: i['id'])

    return render(request,
                  'questions_list.html',
                  {'questions': sorted_qb}
                 )


@login_required(login_url=reverse_lazy('login_view'))
@user_passes_test(user_check,
                  login_url=reverse_lazy('permission_denied'))
def get_question_detail(request,pk):
    """ Question Detail View function."""
    context =  {}
    try:
        question = models.Question.objects.get(id=pk)
        context['question'] = question
    except models.Question.DoesNotExist:
        pass

    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            if request.POST['answer'] == question.answer.answer:
                team_question = models.TeamQuestion.objects.get(
                    question=question,
                    team=request.user.team
                )
                # print(timezone)
                end_time = datetime.now(timezone.utc).astimezone()
                team_question.ended_at = end_time
                diff = team_question.ended_at - team_question.started_at
                # print(diff)
                team_question.time_taken = diff
                team_question.is_completed = True
                team_question.save()

                #save to team model
                team_instance = models.Team.objects.get(id=request.user.team.id)
                # print(points[0])
                # print("Saving time to team")
                # print(team_instance.team_name)
                team_instance.last_question_time = end_time
                team_instance.save()

                # redirects to questions list on success.
                data = "{} Answered  Question Number {}".format(str(request.user.team), str(team_question.question.id))
                r.set('answer_action', data)
                user_key = '{}-key'.format(request.user.team)
                current_action = "Answered Question Number{}".format(question.id)
                r.set(user_key, current_action)
                smsg = "Success !!! Answered Question Number {}".format(str(team_question.question.id))
                messages.success(request, _(smsg))

                return redirect('questions_list')
            messages.warning(request, _("Sorry wrong attempt"))
        # redirects to question detail page on wrong attempt.
        return redirect('question_detail', pk=question.pk)

    if request.method == 'GET':
        user_key = '{}-key'.format(request.user.team)
        current_action = "Standing in Question Number{}".format(question.id)
        r.set(user_key, current_action)
        tq = models.TeamQuestion.objects.filter(
            question=question,
            team=request.user.team).exists()
        if tq:
            team_question = models.TeamQuestion.objects.get(
                question=question,
                team=request.user.team
            )
            context['team_question'] = team_question
            data = "{} Reopened Question Number {}".format(str(request.user.team), str(question.id))
            r.set('question_action', data)
        else:
            team_question = models.TeamQuestion.objects.create(
                team=request.user.team,
                question=question,
                base_points=question.question_points,
                gain_points=question.question_points,
                started_at = datetime.now()
            )
            context['team_question'] = team_question
            data = "{} opened First time Question Number {}".format(str(request.user.team), str(question.id))
            r.set('question_action', data)

        context["question_has_file"] = False
        context["question_has_image"] = False
        file_path = question.question_file_path.strip()
        # fp = (settings.CTF_DIR + "/" + file_path).replace('\\','/')
        # print(fp)
        if file_path:
            # if os.path.exists(fp):
            context["question_has_file"] = True
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.jiff')):
                context["question_has_image"] = True


        context['clue_added'] = True
        if question.question_has_clue:
            clues_count = models.Clue.objects.filter(question=question).count()
            # print(clues_count)
            if clues_count == team_question.clue_version:
                taken_clues = models.Clue.objects.filter(
                    question=question)[:team_question.clue_version]
                context['clue_exist'] = False
                context['taken_clues'] = taken_clues
            else:
                clue = models.Clue.objects.filter(
                    question=question)[team_question.clue_version]
                taken_clues = models.Clue.objects.filter(
                    question=question)[:team_question.clue_version]
                context['clue'] = clue
                context['clue_exist'] = True
                context['taken_clues'] = taken_clues
        else:
            clue = _("Sorry No Clue for this Question")
            context['clue_added'] = False
        form = AnswerForm()
        context['form'] = form
        return render(request, 'question_detail.html',context)



@login_required(login_url=reverse_lazy('login_view'))
@user_passes_test(user_check,
                  login_url=reverse_lazy('permission_denied'))
@never_cache
def get_clue(request, pk):
    """ Get  Clue View."""
    id=pk
    question_instance = models.Question.objects.get(id=id)
    user_key = '{}-key'.format(request.user.team)
    current_action = "Taking Clue For Question Number{}".format(question_instance.id)
    r.set(user_key, current_action)
    team_question = models.TeamQuestion.objects.get(
        question=question_instance,
        team=request.user.team
    )
    clue = models.Clue.objects.filter(
        question=question_instance)[team_question.clue_version]
    # update team clue version
    team_question.clue_version = team_question.clue_version +1
    team_question.save()
    # update team gain points
    team_question.update_gain_points(team_question, clue.clue_points)
    # redirects to quesiton page.
    return redirect('question_detail', pk=id)



# note : we are not using it.
# @login_required(login_url=reverse_lazy('login_view'))
# @user_passes_test(user_check,
#                   login_url=reverse_lazy('permission_denied'))
# def team_dash_board(request):
#     """
#     Team dash board view
#     displays total attempted questions with points.
#     """
#     team = models.Team.objects.all_with_prefetch_details(user=request.user)
#     return render(request, 'team_dash_board.html', {'team': team})


class TeamDashBoard(DetailView):
    """
    Team dash board view
    displays total attempted questions with points.
    """
    template_name = 'team_score_board.html'
    model = models.Team
    context_object_name = 'team'

    def dispatch(self, request, *args, **kwargs):
        """ allowing to access only requested team."""
        team =self.request.user.team
        obj=self.get_object()
        print(obj)
        if team != obj:
            return redirect('team_dash_board', pk=team.id)
        user_key = '{}-key'.format(request.user.team)
        current_action = "Watching Score Board"
        r.set(user_key, current_action)
        return super(TeamDashBoard, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super(TeamDashBoard, self).get_object(queryset=queryset)
        if obj is None:
            raise Http404("Team Profile is Not Found")
        return obj

    def get(self,request,*args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            raise Http404('Team Profile is not found')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        team_profile = self.model.objects.all_with_prefetch_details()
        return team_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solved_questions_number'] = models.TeamQuestion.objects.filter(
            team=self.request.user.team,
            is_completed=True).count()
        team_points = models.TeamQuestion.objects.filter(
            team=self.request.user.team,
            is_completed=True).aggregate(Sum('gain_points'))
        context['total_points'] = team_points['gain_points__sum']
        team_questions =  models.TeamQuestion.objects.filter(
            team=self.request.user.team
        )
        # print(team_questions)
        # questions = []
        # question ={}
        # for q in team_questions:
        #     question['id'] = q.question.id
        #     question['gain_points'] = q.gain_points
        #     question['base_points'] = q.base_points
        #     if q.is_completed:
        #         question['remark'] = 'Congratulations'
        #         question['status'] = 'Completed'
        #         questions.append(question)
        #         question = {}
        #         # print(q.time_taken)
        #     else:
        #         question['remark'] = 'Try Some Clue'
        #         question['status'] = 'In Process'
        #         questions.append(question)
        #         question = {}
        
        # context['solved_questions'] = questions
        context['form'] = MemberForm
        #
        # context['form_action_url'] = reverse_lazy('add_team_member')
        return context


#@login_required(login_url=reverse_lazy('login_view'))
#@user_passes_test(super_user_check,
#                  login_url=reverse_lazy('permission_denied'))
# def team_rankings(request):
#     """
#     Total Team Rankings for admin.
#     """
#     context=  {}
#     context['url'] = '/events/'
#     # context['last_id'] = get_current_event_id(['time'])
#     # context['question_id'] = get_current_event_id(['begin'])
#     return render(request,
#                   'event.html',
#                   context
#                  )

@login_required(login_url=reverse_lazy('login_view'))
@user_passes_test(super_user_check,
                 login_url=reverse_lazy('permission_denied'))
def admin_dashboard(request):
    context = {}
    scores = models.TeamQuestion.objects.filter(is_completed=True)
    # print(scores)
    team_scores = []
    results = scores.values('team__team_name', 'team__last_question_time').annotate(count=Sum('gain_points')).order_by('-count','team__last_question_time')
    for i, res in enumerate(results):
        res["rank"] = i + 1
        # print(res)
        team_scores.append(res)
    # print(team_scores)

    #get data from team model
    # teams_with_points = models.Team.objects.filter(total_points__gte=0)
    # team_scores = list(teams_with_points.values('team__team_name').annotate(count=Sum('gain_points')).order_by('-count'))
    # print(teams_with_points)
    context['team_scores'] = team_scores
    return render(request, 'team_scores.html',context)


# import random
# import json

# def _send_worker():
#     while True:
#         total_page = 'hi'
        # if r.exists('question_action'):
        #     question_action = r.get('question_action').decode('utf-8')
        # else:
        #     question_action = 'No Action'

        # if r.exists('answer_action'):
        #     answer_action = r.get('answer_action').decode('utf-8')
        # # print(answer_action)
        # else:
        #     answer_action = 'No Action'
        # scores = models.TeamQuestion.objects.filter(is_completed=True)
        # print(scores)
        # team_scores = list(scores.values('team__team_name').annotate(count=Sum('gain_points')).order_by('-count'))
        # data = json.dumps(team_scores)
        # _table_start = '<div class="container"><div class="row"></div> <div class="col-lg-4"><table class="table"><thead class="bg-primary"><tr><td>Team</td><td>Score</td></tr></thead>'
        # _body_data = '<tr><td>{}</td><td>{}</td></tr>'
        # _table_end = '</tr></thead></table></div>'
        # for i in range(len(team_scores)):
        #     instance = '<tr><td>{}</td><td>{}</td></tr>'.format(team_scores[i]['team__team_name'], team_scores[i]['count'])
        #     _table_start = _table_start + instance
        # _table_start = _table_start + _table_end
        # print("a")
        # _html_data = '<div class="container" style="margin-top:5%;"> <div class="row"><div class="col-md-4">'
        # _table_start = '<table class="table"><thead class="bg-primary"><tr><td>Team</td><td>Score</td></tr></thead>'
        # for i in range(len(team_scores)):
        #     instance = '<tr><td>{}</td><td>{}</td></tr>'.format(team_scores[i]['team__team_name'], team_scores[i]['count'])
        #     _table_start = _table_start + instance
        # _table_end = '</tr></thead></table></div>'
        # _table_start = _table_start + _table_end
        # _html_data = _html_data+_table_start

        # _top_three_data = '<div class="col-lg-4"><div class="card">'
        # _top_three_data = '<div class="col-lg-4"><div class="row">'
        # _top_three_end = '</div></div>'
        # for i in range(3):
        #     inner_data = '<div class="col-lg-12 col-md-12" style="margin-top:2%;"></div>'

        #     _top_three_data = _top_three_data + inner_data
        # _top_three_data = _top_three_data+_top_three_end
        # _html_data = _html_data + _top_three_data


        # _actions_data = '<div class="col-lg-4 col-md-4">'
        # _inner_action_data1 = '<div class="e-alert snack sky ePull" style="margin-top:2%;"><h4>{}</h4></div>'.format(question_action)
        # _inner_action_data2 = '<div class="e-alert snack success" style="margin-top:2%;"><h4>{}</h4></div>'.format(answer_action)
        # _actions_end = '</div>'
        # _actions_data = _actions_data+_inner_action_data1+_inner_action_data2+_actions_end
        # _html_data = _html_data + _actions_data

        # _second_section = '<div class="container"><div class="row">'
        # for i in range(len(team_scores)):
        #     _team_action_key = team_scores[i]['team__team_name']+'-key'
        #     if r.exists(_team_action_key):
        #         _team_action = r.get(_team_action_key).decode('utf-8')
        #     else:
        #         _team_action = 'No Actions Yet.'
        #     _team_data_start = '<div class="col-lg-4 col-md-4 e-card" style="margin:1%;"><div cass="e-card">\
        #                         <div class="card-body"><h5 class="card-title text-primary">{}</h5><h6>action: {}</h6>\
        #                         <a class="e-btn purple inverted">Details</a>&emsp;&emsp;&emsp;&emsp;\
        #                         <a class="e-btn danger inverted danger">Points:<span class="text-primary"> {}</span></a></div></div></div>'.format(team_scores[i]['team__team_name'], _team_action, team_scores[i]['count'])


        #     _second_section = _second_section + _team_data_start
        # _second_section_end = '</div></div>'
        # _second_section = _second_section + _second_section_end
        # print("b")
        # print("hello")
        # total_page = _html_data + _second_section
        # send_event('time', 'message',total_page)
        # time.sleep(1)




# def _db_ready():
#     from django.db import DatabaseError
#     from django_eventstream.models import Event

#     try:
#         Event.objects.count()
#         return True
#     except DatabaseError:
#         return False

# if _db_ready():
#     threds = []
#     send_thread = threading.Thread(target=_send_worker)
#     send_thread.daemon = True
    # send_thread.start()


# note : we are ot using below view.
# @login_required(login_url=reverse_lazy('login_view'))
# @user_passes_test(user_check,
#                   login_url=reverse_lazy('permission_denied'))
# def answer_question(request):
#     form = AnswerForm(request.POST)
#     print(form)
#     question = models.Question.objects.get(id=request.POST['question'])
#     if form.is_valid():
#         if request.POST['answer'] == question.answer:
#             return redirect('questions_list')
#         else:
#             message.warning(request, _("Sorry Wrong Attempt."))
#     return redirect('question_detail', pk=instance_question.id)



class TeamRegisterView(FormView):
    form_class = TeamCreateForm
    template_name = 'team_register.html'


    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            print("is superuser")
            return super(TeamRegisterView, self).dispatch(request, *args, **kwargs)
        elif request.user.is_authenticated:
            print("is user")
            return HttpResponseRedirect(reverse('landing_page'))
        else:
            print("not user")
            return HttpResponseRedirect(reverse('login_view'))

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('login_view'))

    def form_invalid(self, form):
        print(form.errors)

team_register = TeamRegisterView.as_view()


def registration_closed(request):
    return render(request, 'registration_closed.html')


# @login_required
# def add_team_member(request):
#     if request.method == 'POST':
#         form = MemberForm(request.POST)
#         if form.is_valid():
#             member = form.cleaned_data['member']
#             member_instance = models.Member.objects.create(
#                 full_name=member,
#             )
#             team_member = models.TeamMember.objects.create(
#                 team=request.user.team,
#                 member=member_instance,
#             )
#             return redirect('team_dash_board', pk=request.user.team.id)

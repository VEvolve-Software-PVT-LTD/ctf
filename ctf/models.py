"""
Author: Balaraju M
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class TimeStamp(models.Model):
    """
    TimeStamp model is a reusable abstract model.
    Other models can utilize TimeStamp model.
    """
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    

class Member(TimeStamp):
    """
    Member model will store details of members.
    Who can further can join into teams to contest into event.
    Currently Member model only storing full_name only.
    """
    full_name = models.CharField(
        _("Full Name"), 
        max_length=200
    )
    
    def __str__(self):
        return self.full_name
    
    def get_name(self):
        """ returns name of the user """
        return self.full_name
    
    class Meta:
        
        verbose_name = _("Member")
        verbose_name_plural = _("Members")

    
class TeamManager(models.Manager):
    """
    TeamManager is custom model manager.
    """
    def all_with_prefetch_details(self):
        qs = self.get_queryset()
        return qs.prefetch_related('team_members', 
                                   'team_questions')
    
    
class Team(TimeStamp):
    """
    Team model will store name of the Team to contest in event.
    Members can join into team,With admin permissions.
    Team model has a one-to-one relationship with user model,
    One team can have only one user credentials to login.
    All Team members can login into contest by using same credentials.
    Currently Team model storing only team_name required field.
    """
    team_name = models.CharField(
        _("Team Name"),
        max_length=200,
        unique=True
    )
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE
    )
    last_spoken_to = models.ForeignKey(
        User,
        null=True,
        related_name='help_chats',
        on_delete=models.SET_NULL,
    )
    objects = TeamManager()
    
    def __str__(self):
        return self.team_name
    
    def get_name(self):
        """ returns team name."""
        return self.team_name

    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
    
    
class TeamMember(TimeStamp):
    """
    TeamMember model will store details of team members.
    Member can join into team with admin permissions.
    Team has many relation with model.One team can contian
    N number of memebers with one user credits only.
    """
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        verbose_name=_("Team"), 
        related_name='team_members'
    )
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        verbose_name=_("Team Member"), 
        related_name='team_members'
    )
    
    def __str__(self):
        return '{}-{}'.format(str(self.team), str(self.member))
    
    class Meta:
        verbose_name = _("Team Memeber")
        verbose_name_plural = _("Team Memebers")

    
class Question(TimeStamp):
    """
    Question model will store contest quesiton details.
    question_text, question_points, question_has_clue are
    required fields.Admin can create questions in admin panel
    with admin credentials.
    """
    question_text = models.TextField(
        _("Question")
    )
    question_points = models.PositiveIntegerField(
        _("Question Points")
    )
    question_has_clue = models.BooleanField(
        _("Question Has Clue"),
        default=True
    )
    
    def __str__(self):
        return self.question_text
    

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        
        
class Answer(TimeStamp):
    """
    Answer Model will store answers for event questions.
    answer model has a one-to-one relationship with question 
    model.One question will have only one answer, reverse true.
    answer,question are required fields.
    """
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name='answer',
        verbose_name=_("Question"),
    )
    answer = models.CharField(
        _("Answer"),
        max_length=500
    )
    
    def __str__(self):
        return '{}'.format(str(self.question))
    
    class Meta:
        verbose_name = _("Answer")
        verbose_name = _("Answers")

        
class Clue(TimeStamp):
    """
    Clue Model will store contest question clues.
    Clue model has many relationship with Question.
    One Question can have many clues.
    question and clue_text, clue_points are required fields.
    """
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE,
        related_name='clues',
        verbose_name=_("Question")
    )
    clue_text = models.CharField(
        _("Clue"),
        max_length=500,
    )
    clue_points = models.PositiveIntegerField(
        _("Clue Points")
    )
    
    def __str__(self):
        return str(self.question)

    class Meta:
        verbose_name = _("Clue")
        verbose_name_plural = _("Clues")
        
        
class TeamQuestion(TimeStamp):
    """
    Team Question Model will store team attempted questions.
    Team model has many relation with Question model.
    One Team can attempts many questions.
    base_points: attempted question base points
    gain_points: team gain points which will reduce on
    taking clue, w.r.t clue points.clue_version is a 
    indication for number to know number of clues taken.
    """
    question = models.ForeignKey(
        Question, 
        related_name='team_questions', 
        verbose_name=_("Question"),
        on_delete=models.CASCADE
    )
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='team_questions',
        verbose_name=_("Team")
    )
    base_points = models.PositiveIntegerField()
    gain_points = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.TimeField(null=True, blank=True)
    clue_version = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    def __str__(self):
        return '{}-{}'.format(str(self.question), str(self.team))
    
    
    def update_clue_version(self):
        """ updates the clue version on taking clue."""
        self.clue_version = self.clue_version+1
        self.save()
        
    @classmethod    
    def update_gain_points(cls,tq,cp):
        """ updates gain_points on taking clue."""
        team_question = TeamQuestion.objects.get(id=tq.id)
        team_question.gain_points = team_question.gain_points - cp
        team_question.save()
        
    def completed(self):
        """update question status on submit answer."""
        self.is_completed = True
        self.ended_at = datetime.now()
        self.save()
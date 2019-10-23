from django.contrib import admin
from ctf import models

class TeamAdmin(admin.ModelAdmin):
    # exclude('question_points', 'question_has_clue')
    list_display = ('team_name', 'user',)

admin.site.register(models.Member)
admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.TeamMember)

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer',)

admin.site.register(models.Question)
admin.site.register(models.Answer, AnswerAdmin)
admin.site.register(models.Clue)

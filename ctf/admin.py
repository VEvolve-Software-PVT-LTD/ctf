from django.contrib import admin
from ctf import models


admin.site.register(models.Member)
admin.site.register(models.Team)
admin.site.register(models.TeamMember)
admin.site.register(models.Question)
admin.site.register(models.Answer)
admin.site.register(models.Clue)
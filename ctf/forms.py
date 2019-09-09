"""
Author: Balaraju M.
"""
from django import forms
from django.utils.html import strip_tags
from ctf import models
from django.contrib.auth.models import User

class AnswerForm(forms.Form):
    """ Answer form."""
    answer = forms.CharField(widget=forms.Textarea)
    
    def clean(self):
        """ clean team submitted answer """
        super().clean()
        strip_tags(self.cleaned_data['answer'])
        return self.cleaned_data
   



class TeamCreateForm(forms.ModelForm):

	error_messages = {
		'invalid_team': 'Team Name Already Taken Please choose another.'
	}
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput())
	instance_member = forms.CharField(required=True)

	class Meta:
		model = models.Team
		fields = ('team_name',)


	def clean_team_name(self):
		tn = self.cleaned_data.get('team_name')
		tn_check = models.Team.objects.filter(team_name=tn).exists()
		if tn_check:
			raise forms.ValidationError(
				self.error_messages['invalid_team'],
				code='invalid_team',
			)
		return tn

	def save(self, commit=True):
		instance = super().save(commit=False)
		user_instance = User.objects.create(
			username=self.cleaned_data['username']
		)
		user_instance.set_password(self.cleaned_data['password'])
		user_instance.save()
		member = models.Member.objects.create(
			full_name=self.cleaned_data['instance_member']
		)
		if commit:
			instance.user = user_instance
			instance.save()
			team_member = models.TeamMember.objects.create(
				team=instance,
				member=member,
			)
			return instance


class MemberForm(forms.Form):
	member = forms.CharField(required=True)

	def clean(self):
		super().clean()
		strip_tags(self.cleaned_data['member'])
		return self.cleaned_data
   
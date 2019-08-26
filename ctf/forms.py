"""
Author: Balaraju M.
"""
from django import forms
from django.utils.html import strip_tags


class AnswerForm(forms.Form):
    """ Answer form."""
    answer = forms.CharField(widget=forms.Textarea)
    
    def clean(self):
        """ clean team submitted answer """
        super().clean()
        strip_tags(self.cleaned_data['answer'])
        return self.cleaned_data
   
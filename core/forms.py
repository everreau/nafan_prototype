from django import forms
from django.forms import ModelForm

from .models import FindingAid

class DACSForm(ModelForm):
    # subject headers
    class Meta:
        model = FindingAid
        fields = ('repository',
                  'record_type',
                  'title',
                  'scope_and_content',
                  'ark',
                  'reference_code',
                  'date',
                  'extent',
                  'governing_access',
                  'rights',
                  'creator',
                  'languages',
                  'repository_link',
                  'snac',
                  'wiki',
                  'digital_link',
                  'revision_notes',)
        widgets = {'repository': forms.HiddenInput(),
                   'record_type': forms.HiddenInput()}

class EADForm(ModelForm):
    class Meta:
        model = FindingAid
        fields = ('associated_file',)
        widgets = {'repository': forms.HiddenInput()}

class MARCForm(ModelForm):
    class Meta:
        model = FindingAid
        fields = ('associated_file',)
        widgets = {'repository': forms.HiddenInput()}

class PDFForm(forms.Form):
    class Meta:
        fields = ('repository',
                  'record_type',
                  'title',
                  'revision_notes',
                  'associated_file',)
        widgets = {'repository': forms.HiddenInput(),
                   'record_type': forms.HiddenInput()}


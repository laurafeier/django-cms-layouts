from django import forms
from .models import Layout


class LayoutForm(forms.ModelForm):

    class Meta:
        fields = ()
        model = Layout

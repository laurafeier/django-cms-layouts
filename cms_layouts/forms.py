from django import forms
from .models import Layout


class LayoutForm(forms.ModelForm):

    class Meta:
        # exclude all fields
        # leave only from_page since is readony
        exclude = ('content_type', 'object_id', 'layout_type')
        model = Layout

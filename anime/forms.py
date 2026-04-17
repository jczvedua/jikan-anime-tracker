from django import forms
from .models import AnimeList

class AnimeListForm(forms.ModelForm):
    progress = forms.IntegerField(min_value=0, required=False)
    score = forms.IntegerField(min_value=1, max_value=10, required=False)
    
    class Meta:
        model = AnimeList
        fields = ["status", "progress", "score"]

    def clean_progress(self):
        progress = self.cleaned_data.get("progress")
        total = self.instance.total_episodes

        if progress is None or total is None:
            return progress
        
        if progress > total:
            raise forms.ValidationError(
                f"Progress cannot exceed {total}"
            )
        return progress

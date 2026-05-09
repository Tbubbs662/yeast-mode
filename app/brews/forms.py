from django import forms # type: ignore
from .models import Recipe, BrewSession


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'brew_type', 'style', 'description', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brew_type': forms.Select(attrs={'class': 'form-select'}),
            'style': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BrewSessionForm(forms.ModelForm):
    class Meta:
        model = BrewSession
        fields = ['batch_number', 'status', 'brew_date', 'original_gravity', 'final_gravity', 'notes']
        widgets = {
            'batch_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'brew_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'original_gravity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'final_gravity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
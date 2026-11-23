from django import forms # type: ignore
from .models import Recipe, BrewSession, RecipeAdjunct, RecipeGrain, RecipeHop


class RecipeForm(forms.ModelForm):
    # Rendered in their own "Yeast" section after the ingredient formsets,
    # rather than with the main recipe fields.
    YEAST_FIELDS = ('yeast', 'yeast_amount')

    class Meta:
        model = Recipe
        fields = ['name', 'brew_type', 'style', 'target_gravity', 'target_final_gravity', 'description', 'notes', 'yeast', 'yeast_amount']
        labels = {'yeast_amount': 'Packets / vials'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brew_type': forms.Select(attrs={'class': 'form-select'}),
            'style': forms.TextInput(attrs={'class': 'form-control'}),
            'target_gravity': forms.TextInput(attrs={'class': 'form-control'}),
            'target_final_gravity': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'yeast': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Yeast'}),
            'yeast_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': 'e.g. 1', 'aria-label': 'Packets / vials'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['yeast'].empty_label = 'No yeast chosen yet'

    def main_fields(self):
        return [field for field in self if field.name not in self.YEAST_FIELDS]

    def yeast_fields(self):
        return [self[name] for name in self.YEAST_FIELDS]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('yeast_amount') and not cleaned_data.get('yeast'):
            self.add_error('yeast', 'Choose a yeast for this amount.')
        return cleaned_data


class RecipeHopForm(forms.ModelForm):
    class Meta:
        model = RecipeHop
        fields = ['hop', 'amount', 'unit', 'use', 'time']
        widgets = {
            'hop': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Hop'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': 'Amount', 'aria-label': 'Amount'}),
            'unit': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Unit'}),
            'use': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Use', 'data-hop-use': ''}),
            'time': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'min', 'aria-label': 'Time', 'data-hop-time': ''}),
        }


RecipeHopFormSet = forms.inlineformset_factory(
    Recipe, RecipeHop,
    form=RecipeHopForm,
    extra=1,
    can_delete=True,
)


class RecipeGrainForm(forms.ModelForm):
    class Meta:
        model = RecipeGrain
        fields = ['grain', 'amount', 'unit']
        widgets = {
            'grain': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Grain'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': 'Amount', 'aria-label': 'Amount'}),
            'unit': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Unit'}),
        }


RecipeGrainFormSet = forms.inlineformset_factory(
    Recipe, RecipeGrain,
    form=RecipeGrainForm,
    extra=1,
    can_delete=True,
)


class RecipeAdjunctForm(forms.ModelForm):
    class Meta:
        model = RecipeAdjunct
        fields = ['adjunct', 'amount', 'unit', 'added_when']
        labels = {'added_when': 'Added'}
        widgets = {
            'adjunct': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Adjunct'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': 'Amount', 'aria-label': 'Amount'}),
            'unit': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Unit'}),
            'added_when': forms.Select(attrs={'class': 'form-select', 'aria-label': 'Added'}),
        }


RecipeAdjunctFormSet = forms.inlineformset_factory(
    Recipe, RecipeAdjunct,
    form=RecipeAdjunctForm,
    extra=1,
    can_delete=True,
)


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
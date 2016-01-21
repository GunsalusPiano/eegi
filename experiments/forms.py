from django import forms
from django.core.validators import MinLengthValidator

from clones.forms import RNAiKnockdownField
from experiments.models import Experiment, ExperimentPlate
from library.forms import LibraryPlateField
from utils.forms import EMPTY_CHOICE, BlankNullBooleanSelect, RangeField
from worms.forms import (MutantKnockdownField, ScreenTypeChoiceField,
                         WormChoiceField, clean_mutant_query_and_screen_type)


class ScreenStageChoiceField(forms.ChoiceField):
    """Field for choosing Primary, Secondary, etc."""

    def __init__(self, **kwargs):
        if 'choices' not in kwargs:
            choices = ([EMPTY_CHOICE] +
                       list(ExperimentPlate.SCREEN_STAGE_CHOICES))

            kwargs['choices'] = choices

        super(ScreenStageChoiceField, self).__init__(**kwargs)


class TemperatureChoiceField(forms.ChoiceField):
    """Field for selecting a tested temperature."""

    def __init__(self, **kwargs):
        if 'choices' not in kwargs:
            temperatures = (ExperimentPlate.objects.all()
                            .order_by('temperature')
                            .values_list('temperature', flat=True)
                            .distinct())
            choices = [EMPTY_CHOICE] + [(x, x) for x in temperatures]
            kwargs['choices'] = choices

        super(TemperatureChoiceField, self).__init__(**kwargs)


def validate_new_experiment_plate_id(x):
    """
    Validate that x is a valid ID for a new experiment plate.
    """
    if x <= 0:
        raise forms.ValidationError('ExperimentPlate ID must be positive')

    if ExperimentPlate.objects.filter(pk=x).count():
        raise forms.ValidationError('ExperimentPlate ID {} already exists'
                                    .format(x))


class ExperimentFilterFormBase(forms.Form):
    """
    Base class for filtering Experiment and ExperimentPlate instances.
    """

    plate__id = forms.IntegerField(
        required=False, label='Plate ID', help_text='e.g. 32412')

    plate__date = forms.DateField(
        required=False, label='Date', help_text='YYYY-MM-DD')

    plate__temperature = TemperatureChoiceField(
        required=False, label='Temperature')

    plate__screen_stage = ScreenStageChoiceField(
        required=False, label='Screen stage')

    worm_strain = WormChoiceField(required=False)


class ExperimentPlateFilterForm(ExperimentFilterFormBase):
    """Form for filtering ExperimentPlate instances."""

    plate__id__range = RangeField(
        forms.IntegerField, required=False, label='Plate ID range')

    plate__date__range = RangeField(
        forms.DateField, required=False, label='Date range')

    plate__temperature__range = RangeField(
        forms.DecimalField, required=False, label='Temperature range')

    library_stock__plate = LibraryPlateField(
        required=False, label='Library plate', help_text='e.g. II-3-B2')

    is_junk = forms.NullBooleanField(
        required=False, initial=None, label="Has junk",
        widget=BlankNullBooleanSelect)

    field_order = [
        'plate__id', 'plate__id__range',
        'plate__date',  'plate__date__range',
        'plate__temperature', 'plate__temperature__range',
        'worm_strain', 'plate__screen_stage',
        'library_stock__plate', 'is_junk',
    ]

    def clean(self):
        cleaned_data = super(ExperimentPlateFilterForm, self).clean()

        for k, v in cleaned_data.items():
            # Retain 'False' as a legitimate filter
            if v is False:
                continue

            # Ditch empty strings and None as filters
            if not v:
                del cleaned_data[k]

        plate_pks = (Experiment.objects.filter(**cleaned_data)
                     .order_by('plate').values_list('plate', flat=True))

        cleaned_data['experiment_plates'] = (ExperimentPlate.objects
                                             .filter(pk__in=plate_pks))

        return cleaned_data


class ExperimentWellFilterForm(ExperimentFilterFormBase):
    """Form for filtering Experiment instances."""

    id = forms.CharField(required=False, help_text='e.g. 32412_A01')

    well = forms.CharField(required=False, help_text='e.g. A01')

    library_stock = forms.CharField(
        required=False, help_text='e.g. I-3-B2_A01',
        widget=forms.TextInput(attrs={'size': '15'}))

    library_stock__intended_clone = forms.CharField(
        required=False, label='Intended clone', help_text='e.g. sjj_AH10.4',
        widget=forms.TextInput(attrs={'size': '15'}))

    exclude_l4440 = forms.BooleanField(
        required=False, label='Exclude L4440')

    is_junk = forms.NullBooleanField(
        required=False, initial=None, widget=BlankNullBooleanSelect)

    field_order = [
        'id', 'plate__id', 'well',
        'plate__date', 'plate__temperature',
        'worm_strain', 'plate__screen_stage',
        'library_stock', 'library_stock__intended_clone',
        'exclude_l4440', 'is_junk',
    ]

    def clean(self):
        cleaned_data = super(ExperimentWellFilterForm, self).clean()

        if 'exclude_l4440' in cleaned_data:
            exclude_l4440 = cleaned_data['exclude_l4440']
            del cleaned_data['exclude_l4440']
        else:
            exclude_l4440 = None

        for k, v in cleaned_data.items():
            # Retain 'False' as a legitimate filter
            if v is False:
                continue

            # Ditch empty strings and None as filters
            if not v:
                del cleaned_data[k]

        experiments = Experiment.objects.filter(**cleaned_data)

        if exclude_l4440:
            experiments = experiments.exclude(
                library_stock__intended_clone='L4440')

        cleaned_data['experiments'] = experiments
        return cleaned_data


class AddExperimentPlateForm(forms.Form):
    """
    Form for adding a new experiment plate.

    Adding a new experiment plate also adds the corresponding
    expeirment wells.

    This form makes certain assumptions about the experiment plate:
        - it comes from one library plate
        - it has same worm strain in every well
        - the whole plate is or is not junk
    """

    experiment_plate_id = forms.IntegerField(
        required=True,
        validators=[validate_new_experiment_plate_id])
    screen_stage = ScreenStageChoiceField(required=True)
    date = forms.DateField(required=True)
    temperature = forms.DecimalField(required=True)
    worm_strain = WormChoiceField(required=True)
    library_plate = LibraryPlateField(required=True)
    is_junk = forms.BooleanField(initial=False, required=False)
    plate_comment = forms.CharField(required=False)


class ChangeExperimentPlatesForm(forms.Form):
    """
    Form for updating multiple experiment plates.

    Depending on what field(s) are being updated, the corresponding
    experiment wells might be updated as well.

    Keep in mind the following assumptions that will apply if
    updating one of the following fields:
        - each experiment plate comes from one library plate
        - each experiment plate has only one worm strain
        - each experiment plate is or is not junk
    """
    # Plate-level fields
    screen_stage = ScreenStageChoiceField(required=False)
    date = forms.DateField(required=False)
    temperature = forms.DecimalField(required=False)
    comment = forms.CharField(required=False, label='Plate comment')

    # Well-level fields
    worm_strain = WormChoiceField(required=False)
    is_junk = forms.NullBooleanField(
        required=False, initial=None, widget=BlankNullBooleanSelect)

    # Other
    library_plate = LibraryPlateField(required=False)
    clear_plate_comment = forms.BooleanField(required=False)

    field_order = [
        'screen_stage', 'date', 'temperature', 'worm_strain',
        'library_plate', 'is_junk', 'plate_comment', 'well_comment']


class RNAiKnockdownForm(forms.Form):
    """Form for finding wildtype worms tested with a single RNAi clone."""

    rnai_query = RNAiKnockdownField(
        label='RNAi query',
        validators=[MinLengthValidator(1, message='No clone matches')])

    temperature = forms.DecimalField(required=False,
                                     label='Temperature',
                                     help_text='optional')


class MutantKnockdownForm(forms.Form):
    """Form for finding a mutant worm with the control bacteria."""

    mutant_query = MutantKnockdownField()
    screen_type = ScreenTypeChoiceField()

    def clean(self):
        cleaned_data = super(MutantKnockdownForm, self).clean()
        cleaned_data = clean_mutant_query_and_screen_type(self, cleaned_data)
        return cleaned_data


class DoubleKnockdownForm(forms.Form):
    """Form for finding a double knockdown."""

    mutant_query = MutantKnockdownField()
    rnai_query = RNAiKnockdownField(
        label='RNAi query',
        validators=[MinLengthValidator(1, message='No clone matches')])
    screen_type = ScreenTypeChoiceField()

    def clean(self):
        cleaned_data = super(DoubleKnockdownForm, self).clean()
        cleaned_data = clean_mutant_query_and_screen_type(self, cleaned_data)
        return cleaned_data


class SecondaryScoresForm(forms.Form):
    """Form for getting all secondary scores for a worm/screen combo."""

    mutant_query = MutantKnockdownField()
    screen_type = ScreenTypeChoiceField()

    def clean(self):
        cleaned_data = super(SecondaryScoresForm, self).clean()
        cleaned_data = clean_mutant_query_and_screen_type(self, cleaned_data)
        return cleaned_data

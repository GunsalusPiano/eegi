import os

from django import forms
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.utils import timezone

from clones.forms import RNAiKnockdownField
from experiments.models import (Experiment, ExperimentPlate,
                                ManualScore, ManualScoreCode)
from library.forms import LibraryPlateField
from utils.forms import EMPTY_CHOICE, BlankNullBooleanSelect, RangeField
from worms.forms import (MutantKnockdownField, WormChoiceField,
                         clean_mutant_query_and_screen_type)
from worms.models import WormStrain

import time

SCORE_DEFAULT_PER_PAGE = 15

SCREEN_STAGE_CHOICES = [
    (1, 'Primary'),
    (2, 'Secondary'),
]

SCREEN_TYPE_CHOICES = [
    ('SUP', 'Suppressor'),
    ('ENH', 'Enhancer'),
]

SCORING_FORM_CHOICES = [
    ('SUP', 'Suppressor scoring (w/m/s)'),
    ('LEVELS', 'Enhancer secondary (levels)'),
]

IMPOSSIBLE = 'impossible'


##########
# Fields #
##########

class ScreenStageChoiceField(forms.ChoiceField):
    """Field for choosing Primary, Secondary, etc."""

    def __init__(self, **kwargs):
        kwargs['choices'] = [EMPTY_CHOICE] + SCREEN_STAGE_CHOICES
        super(ScreenStageChoiceField, self).__init__(**kwargs)


class ScreenTypeChoiceField(forms.ChoiceField):
    """
    Field defining a screen as SUP or ENH.

    Whether an experiment is SUP/ENH is based on its worm strain's
    restrictive/permissive temperature.
    """

    def __init__(self, **kwargs):
        kwargs['choices'] = [(x, y.lower()) for x, y in SCREEN_TYPE_CHOICES]

        if 'widget' not in kwargs:
            kwargs['widget'] = forms.RadioSelect

        super(ScreenTypeChoiceField, self).__init__(**kwargs)


class ScreenTypeChoiceFieldWithEmpty(forms.ChoiceField):
    """
    Field defining a screen as SUP or ENH.

    Whether an experiment is SUP/ENH is based on its
    worm strain's restrictive/permissive temperature.
    """

    def __init__(self, **kwargs):
        kwargs['choices'] = [EMPTY_CHOICE] + SCREEN_TYPE_CHOICES
        super(ScreenTypeChoiceFieldWithEmpty, self).__init__(**kwargs)


class TemperatureChoiceField(forms.ChoiceField):
    """Field for selecting a tested temperature."""

    def __init__(self, **kwargs):
        temperatures = ExperimentPlate.get_tested_temperatures()
        kwargs['choices'] = [EMPTY_CHOICE] + [(x, x) for x in temperatures]
        super(TemperatureChoiceField, self).__init__(**kwargs)


class ScoringFormChoiceField(forms.ChoiceField):
    """Field for selecting which scoring form (buttons) should display."""

    def __init__(self, **kwargs):
        kwargs['choices'] = [EMPTY_CHOICE] + SCORING_FORM_CHOICES
        super(ScoringFormChoiceField, self).__init__(**kwargs)


class ScoringListChoiceField(forms.ChoiceField):

    def __init__(self, **kwargs):
        kwargs['choices'] = (
            [EMPTY_CHOICE] +
            [(x, x) for x in os.listdir(settings.BASE_DIR_SCORING_LISTS)]
        )
        super(ScoringListChoiceField, self).__init__(**kwargs)


class SingleScoreField(forms.TypedChoiceField):
    """Field for choosing a level of suppression.

    NOTE: avoid ModelChoiceField because there is no clean way to
    include an empty value (for the "unscorable" case) while still
    making the field required and while not setting an initial value.
    """

    def __init__(self, key, junk_to_last=False, **kwargs):
        choices = []
        cant = (IMPOSSIBLE, 'Can\'t')
        for code in ManualScoreCode.get_codes(key):
            choices.append((code.pk, str(code)))

        if junk_to_last:
            choices.insert(len(choices) - 1, cant)
        else:
            choices.append((IMPOSSIBLE, 'Can\'t'))

        kwargs['choices'] = choices

        kwargs['coerce'] = _coerce_to_manualscorecode

        if 'required' not in kwargs:
            kwargs['required'] = True

        if 'widget' not in kwargs:
            kwargs['widget'] = forms.RadioSelect(attrs={'class': 'keyable'})

        super(SingleScoreField, self).__init__(**kwargs)


class MultiScoreField(forms.ModelMultipleChoiceField):
    """Field for selecting auxiliary scores."""

    def __init__(self, key, **kwargs):
        kwargs['queryset'] = ManualScoreCode.get_codes(key)

        if 'widget' not in kwargs:
            kwargs['widget'] = forms.CheckboxSelectMultiple(
                attrs={'class': 'keyable'})

        super(MultiScoreField, self).__init__(**kwargs)


def _coerce_to_manualscorecode(value):
    if value == IMPOSSIBLE:
        return IMPOSSIBLE

    return ManualScoreCode.objects.get(pk=value)


##############
# Validators #
##############

def validate_new_experiment_plate_id(x):
    """Validate that x is a valid ID for a new experiment plate."""
    if x <= 0:
        raise forms.ValidationError('ExperimentPlate ID must be positive')

    if ExperimentPlate.objects.filter(pk=x).count():
        raise forms.ValidationError('ExperimentPlate ID {} already exists'
                                    .format(x))


###################
# Filtering Forms #
###################

class _FilterExperimentsBaseForm(forms.Form):
    """Base for FilterExperimentWellsForm, FilterExperimentPlatesForm, etc."""

    plate__pk = forms.IntegerField(
        required=False, label='Plate ID', help_text='e.g. 32412')

    plate__date = forms.DateField(
        required=False, label='Date', help_text='YYYY-MM-DD')

    '''
    NOTE: When the below field was a TemperatureChoiceField, it caused
    issues when calling ./manage.py subcommands on an empty database.

    (In case you're wonding, why was I calling ./manage.py on an empty
     database? It was to populate an empty database from scratch, by
     running `./manage.py migrate`).

    The error (which I saw both when trying to run `./manage.py migrate`
    and `./manage.py runserver`:

        django.db.utils.ProgrammingError: (1146, "Table
            'eegi.experimentplate' doesn't exist")

    This only causes an issue with Django >=1.9.0. Django 1.8.9 was
    fine. For now, just use a DecimalField instead.
    '''
    plate__temperature = forms.DecimalField(
        required=False, label='Temperature')

    plate__screen_stage = ScreenStageChoiceField(
        required=False, label='Screen stage')

    worm_strain = WormChoiceField(required=False)


class FilterExperimentPlatesForm(_FilterExperimentsBaseForm):
    """Form for filtering ExperimentPlate instances."""

    plate__pk__range = RangeField(
        forms.IntegerField, required=False, label='Plate ID range')

    plate__date__range = RangeField(
        forms.DateField, required=False, label='Date range')

    plate__temperature__range = RangeField(
        forms.DecimalField, required=False, label='Temperature range')

    library_stock__plate = LibraryPlateField(
        required=False, label='Library plate', help_text='e.g. II-3-B2')

    is_junk = forms.NullBooleanField(
        required=False, initial=None, label='Has junk',
        widget=BlankNullBooleanSelect)

    field_order = [
        'plate__pk', 'plate__pk__range',
        'plate__date',  'plate__date__range',
        'plate__screen_stage',
        'plate__temperature', 'plate__temperature__range',
        'worm_strain',
        'library_stock__plate', 'is_junk',
    ]

    def process(self):
        cleaned_data = self.cleaned_data
        _remove_empties_and_none(cleaned_data)
        plate_pks = (Experiment.objects.filter(**cleaned_data)
                     .order_by('plate').values_list('plate', flat=True))
        return ExperimentPlate.objects.filter(pk__in=plate_pks)


class FilterExperimentWellsForm(_FilterExperimentsBaseForm):
    """Form for filtering Experiment instances."""

    pk = forms.CharField(required=False, help_text='e.g. 32412_A01',
                         label='Experiment ID')

    screen_type = ScreenTypeChoiceFieldWithEmpty(required=False)

    library_stock = forms.CharField(
        required=False, help_text='e.g. I-3-B2_A01',
        widget=forms.TextInput(attrs={'size': '15'}))

    library_stock__intended_clone = forms.CharField(
        required=False, label='Intended clone', help_text='e.g. sjj_AH10.4',
        widget=forms.TextInput(attrs={'size': '15'}))

    is_junk = forms.NullBooleanField(
        required=False, initial=None, widget=BlankNullBooleanSelect)

    exclude_no_clone = forms.BooleanField(
        required=False, label='Exclude (supposedly) empty wells')

    exclude_l4440 = forms.BooleanField(
        required=False, label='Exclude L4440')

    field_order = [
        'pk', 'plate__pk', 'well', 'plate__date', 'plate__screen_stage',
        'screen_type', 'plate__temperature',
        'worm_strain', 'library_stock', 'library_stock__intended_clone',
        'exclude_no_clone', 'exclude_l4440', 'is_junk',
    ]

    def process(self):
        cleaned_data = self.cleaned_data

        exclude_no_clone = cleaned_data.pop('exclude_no_clone')
        exclude_l4440 = cleaned_data.pop('exclude_l4440')
        screen_type = cleaned_data.pop('screen_type')

        _remove_empties_and_none(cleaned_data)
        experiments = Experiment.objects.filter(**cleaned_data)

        if exclude_no_clone:
            experiments = experiments.exclude(
                library_stock__intended_clone__isnull=True)

        if exclude_l4440:
            experiments = experiments.exclude(
                library_stock__intended_clone='L4440')

        # Must be done last, since it post-processes the query
        if screen_type:
            experiments = _limit_to_screen_type(experiments, screen_type)

        return experiments

class ProcessContactSheetForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(ProcessContactSheetForm, self).__init__(*args,**kwargs)
        for row in "ABCDEFGH":
            for col in range(1, 13):
                self.fields[row+format(col,'02d')] = forms.BooleanField(required=False)
            
    

# This inherits the plate__pk, plate__date, plate__temperature,
# plate__screen_stage, and worm strain from the base form.
class FilterExperimentWellsToScoreForm(_FilterExperimentsBaseForm):
    """Form for filtering experiment wells to score."""

    score_form_key = ScoringFormChoiceField(label='Which buttons?')

    scoring_list = ScoringListChoiceField(required=False,
                                          label='Limit to file?')

    gene =  forms.CharField(required=False, help_text = 'Gene symbol, e.g. mbk-2', label='Limit to gene?')

    pk = forms.CharField(required=False, help_text='e.g. 32412_A01',
                         label='Experiment ID')

    plate__pk__range = RangeField(
        forms.IntegerField, required=False, label='Plate ID range')

    plate__date__range = RangeField(
        forms.DateField, required=False, label='Date range')

    plate__temperature__range = RangeField(
        forms.DecimalField, required=False, label='Temperature range')

    screen_type = ScreenTypeChoiceFieldWithEmpty(required=False)

    is_junk = forms.NullBooleanField(
        required=False, initial=False, widget=BlankNullBooleanSelect)

    exclude_no_clone = forms.BooleanField(
        required=False, initial=True, label='Exclude (supposedly) empty wells')

    exclude_l4440 = forms.BooleanField(
        required=False, initial=True, label='Exclude L4440')

    images_per_page = forms.IntegerField(
        required=True, initial=SCORE_DEFAULT_PER_PAGE,
        widget=forms.TextInput(attrs={'size': '3'}))

    unscored_by_user = forms.BooleanField(
        required=False, initial=True,
        label='Exclude if already scored by you')

    randomize_order = forms.BooleanField(required=False, initial=True)

    score_only_4_reps = forms.BooleanField(
        required=False, initial=False, label='Score only 4 replicates')

    exclude_n2 = forms.BooleanField(
        required=False, initial=True, label='Exclude N2')

    score_abridged_set = forms.BooleanField(required=False, initial=False, label="Score Abridged Set",
        help_text="Score manually curated set of experiments")

    is_interesting = forms.BooleanField(required=False, initial=True, label='Is Interesting')

    field_order = [
        'score_form_key', 'scoring_list', 'images_per_page',
        'unscored_by_user', 'randomize_order', 'score_only_4_reps', 'score_abridged_set'
        'exclude_n2', 'exclude_l4440', 'exclude_no_clone', 'is_junk', 'is_interesting',
        'plate__screen_stage', 'plate__date', 'plate__date__range',
        'screen_type', 'plate__temperature', 'plate__temperature__range',
        'worm_strain', 'pk', 'plate__pk', 'plate__pk__range',
    ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(FilterExperimentWellsToScoreForm, self).__init__(*args, **kwargs)

    # this gets called automatically by the is_valid
    def clean(self):
        cleaned_data = super(FilterExperimentWellsToScoreForm, self).clean()
        if (cleaned_data.get('randomize_order') and
                not cleaned_data.get('unscored_by_user')):
            raise forms.ValidationError(
                'Randomizing order not currently supported when '
                'scoring images you have already scored.')
        return cleaned_data

    # this is a user defined method.
    # process is making the queries to score
    def process(self):
        cleaned_data = self.cleaned_data

        # removing parameters that can not be used to filter the django way
        score_form_key = cleaned_data.pop('score_form_key')
        filename = cleaned_data.pop('scoring_list')
        gene = cleaned_data.pop('gene')
        images_per_page = cleaned_data.pop('images_per_page')
        exclude_no_clone = cleaned_data.pop('exclude_no_clone')
        exclude_l4440 = cleaned_data.pop('exclude_l4440')
        unscored_by_user = cleaned_data.pop('unscored_by_user')
        screen_type = cleaned_data.pop('screen_type')
        randomize_order = cleaned_data.pop('randomize_order')
        score_only_4_reps = cleaned_data.pop('score_only_4_reps')
        score_abridged_set = cleaned_data.pop('score_abridged_set')
        exclude_n2 = cleaned_data.pop('exclude_n2')
        # is_interesting = cleaned_data.pop('is_interesting')
        # is_junk = cleaned_data.pop('is_junk')

        _remove_empties_and_none(cleaned_data)
        experiments = (Experiment.objects
            .filter(**cleaned_data)
            .select_related('library_stock','plate','worm_strain')
            .prefetch_related('manualscore_set')
        )

        if score_abridged_set:
            rnai = ['hc69-E1_A05',
                    'hc69-E1_A09',
                    'hc69-E1_A11',
                    'hc69-E1_B04',
                    'hc69-E1_B12',
                    'hc69-E1_C03',
                    'hc69-E1_C04',
                    'hc69-E1_C10',
                    'hc69-E1_D04',
                    'hc69-E1_E03',
                    'hc69-E1_E04',
                    'hc69-E1_E05',
                    'hc69-E1_F01',
                    'hc69-E1_F03',
                    'hc69-E1_F04',
                    'hc69-E1_F07',
                    'hc69-E1_G01',
                    'hc69-E1_H03',
                    'hc69-E1_H04',
                    'hc69-E1_H11',
                    'hc69-E10_B01',
                    'hc69-E10_F04',
                    'hc69-E11_F04',
                    'hc69-E11_G08',
                    'hc69-E12_B07',
                    'hc69-E12_E05',
                    'hc69-E12_E06',
                    'hc69-E13_C04',
                    'hc69-E13_C08',
                    'hc69-E13_C12',
                    'hc69-E13_D01',
                    'hc69-E13_D06',
                    'hc69-E13_E04',
                    'hc69-E13_F02',
                    'hc69-E13_F05',
                    'hc69-E13_G01',
                    'hc69-E13_H02',
                    'hc69-E13_H09',
                    'hc69-E14_C03',
                    'hc69-E14_D03',
                    'hc69-E14_E04',
                    'hc69-E14_G08',
                    'hc69-E14_G11',
                    'hc69-E15_A09',
                    'hc69-E15_A10',
                    'hc69-E15_A11',
                    'hc69-E15_A12',
                    'hc69-E15_B10',
                    'hc69-E15_B12',
                    'hc69-E15_C04',
                    'hc69-E15_C09',
                    'hc69-E15_C10',
                    'hc69-E15_C11',
                    'hc69-E15_E01',
                    'hc69-E15_E03',
                    'hc69-E15_E04',
                    'hc69-E15_F08',
                    'hc69-E16_B06',
                    'hc69-E16_E02',
                    'hc69-E16_G04',
                    'hc69-E16_G10',
                    'hc69-E17_A09',
                    'hc69-E17_A10',
                    'hc69-E17_A11',
                    'hc69-E17_C04',
                    'hc69-E17_D04',
                    'hc69-E17_D05',
                    'hc69-E17_E06',
                    'hc69-E17_F06',
                    'hc69-E17_G09',
                    'hc69-E17_H06',
                    'hc69-E17_H07',
                    'hc69-E17_H08',
                    'hc69-E17_H09',
                    'hc69-E18_A09',
                    'hc69-E18_B09',
                    'hc69-E18_F01',
                    'hc69-E19_A10',
                    'hc69-E19_B08',
                    'hc69-E19_B09',
                    'hc69-E19_C06',
                    'hc69-E19_C10',
                    'hc69-E19_F10',
                    'hc69-E19_G05',
                    'hc69-E2_A04',
                    'hc69-E2_B06',
                    'hc69-E2_B12',
                    'hc69-E2_C09',
                    'hc69-E2_D07',
                    'hc69-E2_E04',
                    'hc69-E2_E08',
                    'hc69-E20_A04',
                    'hc69-E20_A05',
                    'hc69-E20_A06',
                    'hc69-E20_A07',
                    'hc69-E20_A08',
                    'hc69-E20_A10',
                    'hc69-E20_B03',
                    'hc69-E20_B05',
                    'hc69-E20_B06',
                    'hc69-E20_B07',
                    'hc69-E20_B08',
                    'hc69-E20_B09',
                    'hc69-E20_B10',
                    'hc69-E20_B11',
                    'hc69-E20_C06',
                    'hc69-E20_C07',
                    'hc69-E20_C10',
                    'hc69-E20_C12',
                    'hc69-E20_D04',
                    'hc69-E20_D05',
                    'hc69-E20_D06',
                    'hc69-E20_D07',
                    'hc69-E20_D12',
                    'hc69-E20_E02',
                    'hc69-E20_E05',
                    'hc69-E20_E07',
                    'hc69-E20_E08',
                    'hc69-E20_E12',
                    'hc69-E20_F07',
                    'hc69-E20_F10',
                    'hc69-E20_G06',
                    'hc69-E20_G07',
                    'hc69-E20_G08',
                    'hc69-E20_G09',
                    'hc69-E20_H04',
                    'hc69-E20_H05',
                    'hc69-E20_H07',
                    'hc69-E20_H08',
                    'hc69-E20_H09',
                    'hc69-E20_H10',
                    'hc69-E20_H11',
                    'hc69-E21_A02',
                    'hc69-E21_A07',
                    'hc69-E21_B07',
                    'hc69-E21_C01',
                    'hc69-E21_C03',
                    'hc69-E21_E01',
                    'hc69-E21_E05',
                    'hc69-E21_E06',
                    'hc69-E21_E11',
                    'hc69-E21_F06',
                    'hc69-E21_F08',
                    'hc69-E21_G06',
                    'hc69-E21_G07',
                    'hc69-E21_G09',
                    'hc69-E21_H01',
                    'hc69-E21_H03',
                    'hc69-E21_H06',
                    'hc69-E21_H07',
                    'hc69-E21_H08',
                    'hc69-E22_A01',
                    'hc69-E22_A02',
                    'hc69-E22_A04',
                    'hc69-E22_A06',
                    'hc69-E22_A08',
                    'hc69-E22_B01',
                    'hc69-E22_B02',
                    'hc69-E22_B04',
                    'hc69-E22_B05',
                    'hc69-E22_B08',
                    'hc69-E22_B11',
                    'hc69-E22_C02',
                    'hc69-E22_C03',
                    'hc69-E22_C07',
                    'hc69-E22_C08',
                    'hc69-E22_D05',
                    'hc69-E22_D06',
                    'hc69-E22_D08',
                    'hc69-E22_D10',
                    'hc69-E22_E08',
                    'hc69-E22_E09',
                    'hc69-E22_E10',
                    'hc69-E22_F01',
                    'hc69-E22_F03',
                    'hc69-E22_F05',
                    'hc69-E22_F06',
                    'hc69-E22_F09',
                    'hc69-E22_F12',
                    'hc69-E22_G04',
                    'hc69-E22_G05',
                    'hc69-E22_G08',
                    'hc69-E22_G09',
                    'hc69-E22_G10',
                    'hc69-E22_G11',
                    'hc69-E22_G12',
                    'hc69-E22_H04',
                    'hc69-E22_H05',
                    'hc69-E22_H07',
                    'hc69-E22_H08',
                    'hc69-E22_H10',
                    'hc69-E22_H11',
                    'hc69-E22_H12',
                    'hc69-E23_B07',
                    'hc69-E23_D05',
                    'hc69-E23_E10',
                    'hc69-E23_H07',
                    'hc69-E23_H09',
                    'hc69-E3_A09',
                    'hc69-E3_B06',
                    'hc69-E3_B08',
                    'hc69-E3_B11',
                    'hc69-E3_B12',
                    'hc69-E3_D01',
                    'hc69-E3_D10',
                    'hc69-E3_F07',
                    'hc69-E3_G01',
                    'hc69-E3_G06',
                    'hc69-E3_G08',
                    'hc69-E3_H05',
                    'hc69-E3_H06',
                    'hc69-E3_H08',
                    'hc69-E4_A02',
                    'hc69-E4_A11',
                    'hc69-E4_B10',
                    'hc69-E4_C03',
                    'hc69-E4_C05',
                    'hc69-E4_D03',
                    'hc69-E4_E04',
                    'hc69-E4_E12',
                    'hc69-E4_F04',
                    'hc69-E4_F11',
                    'hc69-E4_F12',
                    'hc69-E4_G09',
                    'hc69-E4_H05',
                    'hc69-E5_A03',
                    'hc69-E5_A05',
                    'hc69-E5_B08',
                    'hc69-E5_C06',
                    'hc69-E5_C10',
                    'hc69-E5_D06',
                    'hc69-E5_E06',
                    'hc69-E5_E10',
                    'hc69-E5_F12',
                    'hc69-E5_G08',
                    'hc69-E5_H02',
                    'hc69-E5_H04',
                    'hc69-E5_H06',
                    'hc69-E5_H07',
                    'hc69-E5_H09',
                    'hc69-E5_H10',
                    'hc69-E6_B07',
                    'hc69-E6_B08',
                    'hc69-E6_D03',
                    'hc69-E6_E09',
                    'hc69-E6_G04',
                    'hc69-E6_G08',
                    'hc69-E6_G10',
                    'hc69-E7_A07',
                    'hc69-E7_A11',
                    'hc69-E7_A12',
                    'hc69-E7_B12',
                    'hc69-E7_C04',
                    'hc69-E7_C12',
                    'hc69-E7_D04',
                    'hc69-E7_D05',
                    'hc69-E7_D08',
                    'hc69-E7_D12',
                    'hc69-E7_E04',
                    'hc69-E7_F04',
                    'hc69-E7_F05',
                    'hc69-E7_F07',
                    'hc69-E7_G02',
                    'hc69-E7_G08',
                    'hc69-E7_G11',
                    'hc69-E8_A01',
                    'hc69-E8_A02',
                    'hc69-E8_B01',
                    'hc69-E8_B12',
                    'hc69-E8_C01',
                    'hc69-E8_C02',
                    'hc69-E8_C03',
                    'hc69-E8_C06',
                    'hc69-E8_C09',
                    'hc69-E8_C12',
                    'hc69-E8_D01',
                    'hc69-E8_D02',
                    'hc69-E8_E02',
                    'hc69-E8_E11',
                    'hc69-E8_F10',
                    'hc69-E8_F11',
                    'hc69-E9_A01',
                    'hc69-E9_A02',
                    'hc69-E9_A03',
                    'hc69-E9_A05',
                    'hc69-E9_B03',
                    'hc69-E9_B04',
                    'hc69-E9_B08',
                    'hc69-E9_B10',
                    'hc69-E9_C02',
                    'hc69-E9_C03',
                    'hc69-E9_C04',
                    'hc69-E9_D03',
                    'hc69-E9_D09',
                    'hc69-E9_D10',
                    'hc69-E9_F04',
                    'hc69-E9_G03',
                    'hc69-E9_G04',
                    'hc69-E9_H04',
                    'hc69-E9_H09',
                    'universal-E1_A01',
                    'universal-E1_A02',
                    'universal-E1_A04',
                    'universal-E1_A06',
                    'universal-E1_A08',
                    'universal-E1_A10',
                    'universal-E1_B01',
                    'universal-E1_B02',
                    'universal-E1_B06',
                    'universal-E1_C01',
                    'universal-E1_C02',
                    'universal-E1_C03',
                    'universal-E1_C04',
                    'universal-E1_C05',
                    'universal-E1_C06',
                    'universal-E1_C07',
                    'universal-E1_C09',
                    'universal-E1_C10',
                    'universal-E1_D02',
                    'universal-E1_D07',
                    'universal-E1_E04',
                    'universal-E1_E09',
                    'universal-E1_E10',
                    'universal-E1_F03',
                    'universal-E1_F04',
                    'universal-E1_F08',
                    'universal-E1_F10',
                    'universal-E1_F12',
                    'universal-E1_G01',
                    'universal-E1_G04',
                    'universal-E1_G07',
                    'universal-E1_G09',
                    'universal-E1_G12',
                    'universal-E1_H02',
                    'universal-E1_H03',
                    'universal-E1_H07',
                    'universal-E1_H11',
                    'universal-E1_H12',
                    'universal-E10_A03',
                    'universal-E10_A04',
                    'universal-E10_A06',
                    'universal-E10_A08',
                    'universal-E10_A10',
                    'universal-E10_B03',
                    'universal-E10_B06',
                    'universal-E10_B12',
                    'universal-E10_C01',
                    'universal-E10_C03',
                    'universal-E10_C08',
                    'universal-E10_D02',
                    'universal-E10_D07',
                    'universal-E10_D10',
                    'universal-E10_E02',
                    'universal-E10_E07',
                    'universal-E10_F10',
                    'universal-E10_F11',
                    'universal-E10_G02',
                    'universal-E10_G05',
                    'universal-E10_G09',
                    'universal-E10_H01',
                    'universal-E10_H04',
                    'universal-E10_H07',
                    'universal-E11_A03',
                    'universal-E11_A06',
                    'universal-E11_A08',
                    'universal-E11_A12',
                    'universal-E11_B01',
                    'universal-E11_B02',
                    'universal-E11_C01',
                    'universal-E11_C03',
                    'universal-E11_C06',
                    'universal-E11_C11',
                    'universal-E11_C12',
                    'universal-E11_D03',
                    'universal-E11_D07',
                    'universal-E11_E04',
                    'universal-E11_E06',
                    'universal-E11_E07',
                    'universal-E11_E09',
                    'universal-E11_F06',
                    'universal-E11_F09',
                    'universal-E11_G02',
                    'universal-E11_G03',
                    'universal-E11_G04',
                    'universal-E11_G05',
                    'universal-E11_G06',
                    'universal-E11_G08',
                    'universal-E11_G09',
                    'universal-E11_G11',
                    'universal-E11_H01',
                    'universal-E11_H06',
                    'universal-E11_H11',
                    'universal-E2_A01',
                    'universal-E2_A02',
                    'universal-E2_A04',
                    'universal-E2_A05',
                    'universal-E2_A09',
                    'universal-E2_A11',
                    'universal-E2_B03',
                    'universal-E2_B10',
                    'universal-E2_B11',
                    'universal-E2_C01',
                    'universal-E2_C02',
                    'universal-E2_C05',
                    'universal-E2_C08',
                    'universal-E2_C09',
                    'universal-E2_C10',
                    'universal-E2_C12',
                    'universal-E2_D02',
                    'universal-E2_D06',
                    'universal-E2_D08',
                    'universal-E2_D09',
                    'universal-E2_D10',
                    'universal-E2_D11',
                    'universal-E2_E01',
                    'universal-E2_E03',
                    'universal-E2_E05',
                    'universal-E2_E11',
                    'universal-E2_F01',
                    'universal-E2_F02',
                    'universal-E2_F03',
                    'universal-E2_F10',
                    'universal-E2_F12',
                    'universal-E2_G01',
                    'universal-E2_G02',
                    'universal-E2_G05',
                    'universal-E2_G09',
                    'universal-E2_G12',
                    'universal-E3_A04',
                    'universal-E3_A06',
                    'universal-E3_A07',
                    'universal-E3_A09',
                    'universal-E3_A10',
                    'universal-E3_A12',
                    'universal-E3_B02',
                    'universal-E3_B03',
                    'universal-E3_B08',
                    'universal-E3_C01',
                    'universal-E3_C02',
                    'universal-E3_C03',
                    'universal-E3_C04',
                    'universal-E3_C06',
                    'universal-E3_C07',
                    'universal-E3_C09',
                    'universal-E3_C10',
                    'universal-E3_C12',
                    'universal-E3_D01',
                    'universal-E3_D03',
                    'universal-E3_D04',
                    'universal-E3_D06',
                    'universal-E3_D07',
                    'universal-E3_D11',
                    'universal-E3_E01',
                    'universal-E3_E03',
                    'universal-E3_E04',
                    'universal-E3_E08',
                    'universal-E3_E12',
                    'universal-E3_F04',
                    'universal-E3_F05',
                    'universal-E3_F07',
                    'universal-E3_F09',
                    'universal-E3_F10',
                    'universal-E3_F12',
                    'universal-E3_G02',
                    'universal-E3_G04',
                    'universal-E3_G05',
                    'universal-E3_G12',
                    'universal-E3_H01',
                    'universal-E3_H02',
                    'universal-E3_H03',
                    'universal-E3_H04',
                    'universal-E3_H05',
                    'universal-E3_H07',
                    'universal-E3_H08',
                    'universal-E3_H09',
                    'universal-E3_H10',
                    'universal-E4_A02',
                    'universal-E4_A03',
                    'universal-E4_A04',
                    'universal-E4_A08',
                    'universal-E4_A09',
                    'universal-E4_B01',
                    'universal-E4_B03',
                    'universal-E4_B05',
                    'universal-E4_B11',
                    'universal-E4_C01',
                    'universal-E4_C02',
                    'universal-E4_C03',
                    'universal-E4_C06',
                    'universal-E4_C08',
                    'universal-E4_C11',
                    'universal-E4_C12',
                    'universal-E4_D01',
                    'universal-E4_D02',
                    'universal-E4_D03',
                    'universal-E4_D06',
                    'universal-E4_D08',
                    'universal-E4_D11',
                    'universal-E4_D12',
                    'universal-E4_E01',
                    'universal-E4_E02',
                    'universal-E4_E05',
                    'universal-E4_E06',
                    'universal-E4_E12',
                    'universal-E4_F01',
                    'universal-E4_F03',
                    'universal-E4_F10',
                    'universal-E4_F12',
                    'universal-E4_G02',
                    'universal-E4_G05',
                    'universal-E4_G06',
                    'universal-E4_G08',
                    'universal-E4_G09',
                    'universal-E4_H01',
                    'universal-E4_H06',
                    'universal-E4_H08',
                    'universal-E4_H10',
                    'universal-E4_H12',
                    'universal-E5_A02',
                    'universal-E5_A04',
                    'universal-E5_A05',
                    'universal-E5_A06',
                    'universal-E5_A07',
                    'universal-E5_A08',
                    'universal-E5_A11',
                    'universal-E5_B01',
                    'universal-E5_B03',
                    'universal-E5_B09',
                    'universal-E5_C01',
                    'universal-E5_C05',
                    'universal-E5_C07',
                    'universal-E5_C08',
                    'universal-E5_C09',
                    'universal-E5_C10',
                    'universal-E5_C11',
                    'universal-E5_C12',
                    'universal-E5_D01',
                    'universal-E5_D03',
                    'universal-E5_D04',
                    'universal-E5_D06',
                    'universal-E5_D08',
                    'universal-E5_D09',
                    'universal-E5_E02',
                    'universal-E5_E03',
                    'universal-E5_E04',
                    'universal-E5_E06',
                    'universal-E5_E07',
                    'universal-E5_E09',
                    'universal-E5_E10',
                    'universal-E5_E11',
                    'universal-E5_F02',
                    'universal-E5_F06',
                    'universal-E5_F10',
                    'universal-E5_G01',
                    'universal-E5_G02',
                    'universal-E5_G05',
                    'universal-E5_G06',
                    'universal-E5_G07',
                    'universal-E5_G09',
                    'universal-E5_H01',
                    'universal-E5_H05',
                    'universal-E5_H06',
                    'universal-E5_H08',
                    'universal-E5_H10',
                    'universal-E5_H12',
                    'universal-E6_B05',
                    'universal-E6_B09',
                    'universal-E6_B12',
                    'universal-E6_C01',
                    'universal-E6_C06',
                    'universal-E6_C10',
                    'universal-E6_D02',
                    'universal-E6_D06',
                    'universal-E6_E06',
                    'universal-E6_E08',
                    'universal-E6_E12',
                    'universal-E6_F11',
                    'universal-E6_G10',
                    'universal-E6_H01',
                    'universal-E7_A03',
                    'universal-E7_A05',
                    'universal-E7_A07',
                    'universal-E7_A08',
                    'universal-E7_A09',
                    'universal-E7_A11',
                    'universal-E7_B02',
                    'universal-E7_B06',
                    'universal-E7_B11',
                    'universal-E7_C04',
                    'universal-E7_C05',
                    'universal-E7_C06',
                    'universal-E7_C08',
                    'universal-E7_C09',
                    'universal-E7_C10',
                    'universal-E7_C11',
                    'universal-E7_D02',
                    'universal-E7_D03',
                    'universal-E7_D05',
                    'universal-E7_D07',
                    'universal-E7_D09',
                    'universal-E7_D11',
                    'universal-E7_D12',
                    'universal-E7_E01',
                    'universal-E7_E03',
                    'universal-E7_E06',
                    'universal-E7_E08',
                    'universal-E7_E09',
                    'universal-E7_F01',
                    'universal-E7_F02',
                    'universal-E7_F03',
                    'universal-E7_F04',
                    'universal-E7_F05',
                    'universal-E7_F07',
                    'universal-E7_F08',
                    'universal-E7_F09',
                    'universal-E7_F11',
                    'universal-E7_F12',
                    'universal-E7_G01',
                    'universal-E7_G05',
                    'universal-E7_G06',
                    'universal-E7_G07',
                    'universal-E7_G08',
                    'universal-E7_H04',
                    'universal-E7_H08',
                    'universal-E7_H10',
                    'universal-E8_A01',
                    'universal-E8_A02',
                    'universal-E8_A05',
                    'universal-E8_A06',
                    'universal-E8_A10',
                    'universal-E8_A12',
                    'universal-E8_B05',
                    'universal-E8_B09',
                    'universal-E8_B11',
                    'universal-E8_B12',
                    'universal-E8_C04',
                    'universal-E8_C08',
                    'universal-E8_C09',
                    'universal-E8_C11',
                    'universal-E8_C12',
                    'universal-E8_D01',
                    'universal-E8_D04',
                    'universal-E8_D05',
                    'universal-E8_D06',
                    'universal-E8_D08',
                    'universal-E8_D10',
                    'universal-E8_D12',
                    'universal-E8_E06',
                    'universal-E8_E07',
                    'universal-E8_E10',
                    'universal-E8_F05',
                    'universal-E8_G03',
                    'universal-E8_G05',
                    'universal-E8_G07',
                    'universal-E8_G10',
                    'universal-E8_H03',
                    'universal-E8_H07',
                    'universal-E8_H09',
                    'universal-E9_A01',
                    'universal-E9_A05',
                    'universal-E9_A08',
                    'universal-E9_A11',
                    'universal-E9_B05',
                    'universal-E9_B07',
                    'universal-E9_B11',
                    'universal-E9_B12',
                    'universal-E9_C02',
                    'universal-E9_C03',
                    'universal-E9_C07',
                    'universal-E9_C08',
                    'universal-E9_C09',
                    'universal-E9_C10',
                    'universal-E9_C11',
                    'universal-E9_C12',
                    'universal-E9_D02',
                    'universal-E9_D04',
                    'universal-E9_D06',
                    'universal-E9_D07',
                    'universal-E9_D09',
                    'universal-E9_D10',
                    'universal-E9_D11',
                    'universal-E9_D12',
                    'universal-E9_E04',
                    'universal-E9_E07',
                    'universal-E9_E10',
                    'universal-E9_E11',
                    'universal-E9_F01',
                    'universal-E9_F05',
                    'universal-E9_F09',
                    'universal-E9_F10',
                    'universal-E9_G02',
                    'universal-E9_G10',
                    'universal-E9_G11',
                    'universal-E9_G12',
                    'universal-E9_H01',
                    'universal-E9_H03']
            experiments = experiments.filter(plate_id__date='2015-07-29', worm_strain_id__gene='emb-8', library_stock__in=rnai)
        else:

            if gene:
                experiments = experiments.filter(worm_strain__gene=gene)

            if exclude_no_clone:
                experiments = experiments.exclude(
                    library_stock__intended_clone__isnull=True)

            if exclude_l4440:
                experiments = experiments.exclude(
                    library_stock__intended_clone='L4440')

            if exclude_n2:
                experiments = experiments.exclude(
                    worm_strain="N2"
                )

        if unscored_by_user:
            score_ids = (
                ManualScore.objects
                .filter(experiment__in=experiments, scorer=self.user)
                .values_list('experiment_id', flat=True))
            experiments = experiments.exclude(id__in=score_ids)

        '''
        If this button is selected, exclude those plates that have four or more scored plates.
        The way I intend on doing it will be to scan all of the experiments and count how many
        of them have a manual score of <4 and pass those through.

        The problem with this is that it will does not consider if > 4 replicates have been marked as junk
        for that session and will need to be executed again.
        '''
        if score_only_4_reps:

            score_ids = ManualScore.objects.all().values_list('experiment_id', flat=True)

            #This is the working query

            replicate_plates = (
                experiments
                .values('well', 'worm_strain_id','library_stock_id',
                'plate__date','plate__temperature')
                .order_by('well', 'worm_strain_id', 'library_stock_id',
                'plate__date', 'plate__temperature')
                .distinct()
            )

            '''
            # test set
            replicate_plates = (
                experiments
                .filter(
                plate__date="2015-05-20",
                plate__temperature=15,
                worm_strain="AR1",
                well="A01",
                library_stock="mr17-E1_A01")
                .values('well', 'worm_strain_id','library_stock_id',
                'plate__date','plate__temperature')
                .order_by()
                .distinct()
            )
            '''


            to_score = []

            for rep in replicate_plates.order_by('?')[:1000]:

                rep_set = (experiments
                    .filter(**rep)
                    .select_related('worm_strain','plate','library_stock')
                    .prefetch_related('manualscore_set')
                )

                reps_scored_already = rep_set.exclude(id__in=score_ids).values('pk')
                count = reps_scored_already.count()
                if count <= 4:
                    continue
                elif count == 8:
                    to_score.extend(rep_set
                        .order_by('?')[:4]
                        .values_list('id', flat=True))
                else:
                    count = count - 4
                    to_score.extend(rep_set
                        .order_by('?')[:count]
                        .values_list('id', flat=True))


            experiments = experiments.filter(id__in=to_score)

        # Special case for Malcolm to score subset defined in a file
        # Trash it or make it able to upload file
        if filename:
            path = os.path.join(settings.BASE_DIR_SCORING_LISTS, filename)

            with open(path, 'r') as f:
                key = f.readline().strip()
                scoring_list = [line.strip() for line in f]

                if key == 'library_stock':
                    experiments = experiments.filter(
                        library_stock__in=scoring_list)

        if randomize_order:
            # Warning: Django docs mentions that `order_by(?)` may be
            # expensive and slow. If performance becomes an issue, switch
            # to another way
            experiments = experiments.order_by('?')

        # Must be done last, since it post-processes the query
        if screen_type:
            experiments = _limit_to_screen_type(experiments, screen_type)

        return {
            'experiments': experiments,
            'score_form': get_score_form(score_form_key),
            'images_per_page': images_per_page,
            'unscored_by_user': unscored_by_user,
        }

def _remove_empties_and_none(d):
    """Remove key-value pairs from dictionary if the value is '' or None."""
    for k, v in d.items():
        # Retain 'False' as a legitimate filter
        if v is False:
            continue

        # Ditch empty strings and None as filters
        if not v:
            del d[k]


def _limit_to_screen_type(experiments, screen_type):
    '''
    Post-process experiments QuerySet such that each experiment was done at its
    worm's SUP or ENH temperature. Since N2 does not have a SUP or ENH
    temperature, N2 will not be in this result.

    Question: Why not just get the SUP/ENH temperature for these experiments'
    worm, and then using `.filter()` with that temperature?

    Answer: That is what I do on queries limited to a single worm strain, e.g.
    for most of the public-facing pages. But these experiment filtering forms
    are meant to be flexible (basically a gateway into the database for GI
    team use only), flexible enough to potentially include multiple strains
    with different SUP/ENH temperatures (e.g. maybe Noah wants to see all
    experiments from one date).

    Question: Why not just join between ExperimentPlate.temperature and
    WormStrain.permissive_temperature / .restrictive_temperature?

    This would involve joining WormStrain on a second field. While easy with
    raw SQL, this is not easy with Django, requiring either 1) soon-to-
    be-deprecated `empty()`, 2) overriding low level query processing in ways
    that are subject to syntax changes, or 3) using `raw()` to write raw SQL.
    While I was tempted to do 3), since these filtering forms are meant to be
    generic and applicable (able to take dozens of possible keys to filter on),
    this one case doesn't warrant losing the readability and protections
    against SQL injection attacks that Django QuerySets provide.
    '''
    # Create a dictionary
    to_temperature = WormStrain.get_worm_to_temperature_dictionary(screen_type)
    filtered = []

    for experiment in experiments.prefetch_related('worm_strain', 'plate'):
        temperature = experiment.plate.temperature
        # print "plate temperature",temperature
        # print "worm strain temperature",to_temperature[experiment.worm_strain]

        if temperature == to_temperature[experiment.worm_strain]:
            filtered.append(experiment)

    return filtered


###################
# Knockdown forms #
###################

class RNAiKnockdownForm(forms.Form):
    """Form for finding wildtype worms tested with a single RNAi clone."""

    rnai_query = RNAiKnockdownField(
        label='RNAi query',
        validators=[MinLengthValidator(1, message='No clone match')])

    temperature = forms.DecimalField(required=False, label='Temperature',
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


##########################
# Secondary Scores forms #
##########################

class SecondaryScoresForm(forms.Form):
    """Form for getting all secondary scores for a worm/screen combo."""

    mutant_query = MutantKnockdownField()
    secondary_mutant_query = MutantKnockdownField(required=False)
    screen_type = ScreenTypeChoiceField()

    def clean(self):
        cleaned_data = super(SecondaryScoresForm, self).clean()
        cleaned_data = clean_mutant_query_and_screen_type(self, cleaned_data)
        return cleaned_data


#################
# Scoring Forms #
#################

def get_score_form(key):
    d = {
        'SUP': SuppressorScoreForm,
        'LEVELS': LevelsScoreForm,
    }
    return d[key]


class ScoreForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ScoreForm, self).__init__(*args, **kwargs)

# THis is the secondary suppressor scoring form
class SuppressorScoreForm(ScoreForm):

    sup_score = SingleScoreField(key='SUP', required=True)
    auxiliary_scores = MultiScoreField(key='AUXILIARY', required=False)

    def clean(self):
        cleaned_data = super(SuppressorScoreForm, self).clean()

        if ('sup_score' in cleaned_data and
                cleaned_data['sup_score'] == IMPOSSIBLE and
                not cleaned_data['auxiliary_scores']):
            raise forms.ValidationError('"Impossible to judge" requires '
                                        'some auxiliary score')
        return cleaned_data

    def process(self):
        cleaned_data = self.cleaned_data
        save_score = _get_save_score(self)

        save_score(cleaned_data.get('sup_score'))

        for code in cleaned_data.get('auxiliary_scores'):
            save_score(code)


# This is the secondary enhancer scoring form (the one where you actually score)
class LevelsScoreForm(ScoreForm):

    mut_hits = SingleScoreField(key='MUT_HITS', required=True, label="Mutant Hits")
    # mut_hits = forms.ChoiceField(choices=MUT_HIT_CHOICES, label="Mutant Hits")
    # emb_score = SingleScoreField(key='EMB_LEVEL', required=True, label="Emb score")
    # ste_score = SingleScoreField(key='STE_LEVEL', required=True, label="Ste score")
    ste_relative_score = SingleScoreField(key='STE_REL_LEVEL', required=True, label="Ste rel.:")
    emb_relative_score = SingleScoreField(key='EMB_REL_LEVEL', required=True, label="Emb rel.:")
    n2_rnai_emb_score = SingleScoreField(key='N2_RNAi_emb', required=True, label="N2 emb:", junk_to_last=True)
    n2_rnai_ste_score = SingleScoreField(key='N2_RNAi_ste', required=True, label="N2 ste:", junk_to_last=True)
    mut_rnai_emb_score = SingleScoreField(key='MUT_RNAi_emb', required=True, label="mut emb:")
    mut_rnai_ste_score = SingleScoreField(key='MUT_RNAi_ste', required=True, label="mut ste:")
    auxiliary_scores = MultiScoreField(key='AUXILIARY', required=False, label="Auxiliary scores:")

    def clean(self):
        cleaned_data = super(LevelsScoreForm, self).clean()

        if (
                # 'emb_score' in cleaned_data and 
                # 'ste_score' in cleaned_data and
                # cleaned_data['emb_score'] == IMPOSSIBLE and
                # cleaned_data['ste_score'] == IMPOSSIBLE and
                cleaned_data['ste_relative_score'] == IMPOSSIBLE and
                cleaned_data['emb_relative_score'] == IMPOSSIBLE and
                cleaned_data['n2_rnai_emb_score'] == IMPOSSIBLE and
                cleaned_data['n2_rnai_ste_score'] == IMPOSSIBLE and
                cleaned_data['mut_rnai_emb_score'] == IMPOSSIBLE and
                cleaned_data['mut_rnai_ste_score'] == IMPOSSIBLE and
                not cleaned_data['auxiliary_scores']):
            raise forms.ValidationError('"Impossible to judge" requires '
                                        'some auxiliary score')
        return cleaned_data

    def process(self):
        cleaned_data = self.cleaned_data
        save_score = _get_save_score(self)

        # save_score(cleaned_data.get('emb_score'))
        # save_score(cleaned_data.get('ste_score'))
        save_score(cleaned_data.get('ste_relative_score'))
        save_score(cleaned_data.get('emb_relative_score'))
        save_score(cleaned_data.get('n2_rnai_ste_score'))
        save_score(cleaned_data.get('n2_rnai_emb_score'))
        save_score(cleaned_data.get('mut_rnai_ste_score'))
        save_score(cleaned_data.get('mut_rnai_emb_score'))
        save_score(cleaned_data.get('mut_hits'))
        for code in cleaned_data.get('auxiliary_scores'):
            save_score(code)


def _get_save_score(form):
    experiment = Experiment.objects.get(pk=form.prefix)

    # Each simultaneously-scored score for this image should get the same
    # timestamp
    time = timezone.now()

    # This overrides the save function, and though it's nested it somehow gets
    # called by save_score
    def save_score(score_code):
        # If it's completely emb, ste is impossible to judge
        # likewise for ste
        if score_code == IMPOSSIBLE:
            return


        # SQL query to delete all misassigned rows
        # delete record from ManualScore record join Experiment on experiment_id = Experiment.id where timestamp >= '2018-04-01' and worm_strain_id != 'N2' and `score_code_id` in (47, 48, 49, 20)

        # if score_code.id in [20,47,48,49]:

        aux = [-14, -13, -12, -11, -10, -19, -9, 
               -7, -5, -4, -3, -2, 7, 8, 10, 11]
        emb_rel = [12, 13, 14, 15, 73]
        ste_rel = [16, 17, 18, 19, 74]
        n2_rnai_ste_cons = [71, 47, 48, 49, 53]
        n2_rnai_emb_cons = [72, 50, 51, 52, 53]
        mut_rnai_ste_cons = [63, 64, 65, 66]
        mut_rnai_emb_cons = [67, 68, 69, 70]
        mut_hits = [54, 55, 56, 57, 58, 59, 60, 61, 62]

        n2_scores = n2_rnai_ste_cons + n2_rnai_emb_cons
        mut_scores = aux + emb_rel + ste_rel + mut_rnai_ste_cons + mut_rnai_emb_cons + mut_hits

        if score_code.id in n2_scores:
            for control in experiment.get_link_to_exact_n2_control():
                control_score = ManualScore(
                    experiment=control, score_code=score_code,
                    scorer=form.user, timestamp=time
                )
                control_score.save()

        elif score_code.id in mut_scores:
            for exp in experiment.get_experiment_replicate_plates():
                exp_score = ManualScore(
                    experiment=exp, score_code=score_code,
                    scorer=form.user, timestamp=time
                )
                exp_score.save()
        
        else:
            score = ManualScore(
                experiment=experiment, score_code=score_code,
                scorer=form.user, timestamp=time)
            score.save()

            # if score_code.id in [63, 64, 65, 66, 67, 68, 69, 70]:
            #     for exp in experiment.get_experiment_replicate_plates():
            #         exp_score = ManualScore(
            #             experiment=exp, score_code=score_code,
            #             scorer=form.user, timestamp=time
            #         )
            #         exp_score.save()
            # else:
            #     score = ManualScore(
            #         experiment=experiment, score_code=score_code,
            #         scorer=form.user, timestamp=time)
            #     score.save()

    return save_score


##################################
# Other database-modifying forms #
##################################

class AddExperimentPlateForm(forms.Form):
    """
    Form for adding a new experiment plate.

    Adding a new experiment plate also adds the corresponding
    experiment wells.

    This form makes certain assumptions about the experiment plate:
        - it comes from one library plate
        - it has same worm strain in every well
        - the whole plate is or is not junk
    """

    experiment_plate_id = forms.IntegerField(
        required=True,
        validators=[validate_new_experiment_plate_id])
    screen_stage = ScreenStageChoiceField(required=True)
    date = forms.DateField(required=True, help_text='YYYY-MM-DD')
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
    date = forms.DateField(required=False, help_text='YYYY-MM-DD')
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


def process_ChangeExperimentPlatesForm_data(experiment_plate, data):
    """
    Helper to apply the ChangeExperimentPlateForm changes to a specific
    plate.

    data should be the cleaned_data from a ChangeExperimentPlatesForm.
    """
    # First update straightforward plate fields
    for key in ('screen_stage', 'date', 'temperature', 'comment',):
        value = data.get(key)

        if value:
            setattr(experiment_plate, key, value)
            experiment_plate.save()

    # Next update plate methods
    if data.get('worm_strain'):
        experiment_plate.set_worm_strain(data.get('worm_strain'))

    if data.get('library_plate'):
        experiment_plate.set_library_stocks(data.get('library_plate'))

    if data.get('is_junk') is not None:
        experiment_plate.set_junk(data.get('is_junk'))

    return


class ScreenSummaryForm(forms.Form):
    """
    This form is used to search scoring results that get fed into a table.


    TODO
        - Add radio button for interesting first pass/detailed/either
    """

    screen_stage = ScreenStageChoiceField(required=False)
    screen_type = ScreenTypeChoiceFieldWithEmpty(required=False)
    gene =  forms.CharField(required=False, help_text = 'Gene symbol, e.g. mbk-2', label='Limit to gene?')



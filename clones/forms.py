from django.utils.safestring import mark_safe
from django import forms

from clones.models import Clone

class CloneSearchField(forms.CharField):
    """
    Field to query for a clone, by clone.pk or its gene targets.

    Since this is meant as generic search field for finding clones,
    if no value is entered, all clones are returned.

    If a value is supplied, only matching clones are returned.
    This match is defined as:
        - the clone whose pk matches the search term
        - if no clone.pk match, any clones with a gene target matching
          the search term (on locus, cosmid, or pk)
        - if no clone.pk match and no target match, an empty list
    """

    def __init__(self, **kwargs):
        if 'help_text' not in kwargs:
            kwargs['help_text'] = ('clone name or gene target '
                                   '(WormBase id, cosmid id, or locus)')

        super(CloneSearchField, self).__init__(**kwargs)

    def to_python(self, value):
        if not value:
            return Clone.objects.all()
        else:
            return Clone.get_clones_from_search_term(value)


class RNAiKnockdownField(CloneSearchField):
    """
    Field to find RNAi clone(s).

    Since this is meant for finding knockdowns,
    L4440 (the control clone with no RNAi effect) is not allowed.

    Since this is meant as a field to define a knockdown page,
    if no value is entered, a ValidationError is raised.

    Otherwise, a match is defined as in CloneSearchField.
    """

    def to_python(self, value):
        if value == 'L4440':
            raise forms.ValidationError('RNAi query cannot be L4440')
        elif not value:
            return None
        else:
            return Clone.get_clones_from_search_term(value)


class CloneSearchForm(forms.Form):
    """Form to search for clones."""

    clone_query = CloneSearchField(required=False)

class GeneSearchForm(forms.Form):
    """Form to search for clones."""

    SEARCH_CHOICES=(
        ('wb_gene_id', mark_safe(u'<strong>WB Gene ID</strong> <em>e.g. \'WBGene00000028\'</em>')),
        ('locus', mark_safe(u'<strong>Locus</strong> <em>e.g. \'abu-5\'</em>')),
        ('clone_id',mark_safe(u'<strong>Clone</strong> <em>e.g. \'sjj_Y105C5A.c\'</em>')),
        ('stock_id', mark_safe(u'<strong>Stock</strong> <em>e.g. \'V-7-B2_B11\'</em>')),
        ('cosmid_id', mark_safe(u'<strong>Cosmid</strong> <em>e.g. \'Y105C5A.4\'</em>')),
    )

    choice_field = forms.ChoiceField(widget=forms.RadioSelect, choices=SEARCH_CHOICES)

    gene_query = forms.CharField(required=False)

    file_field = forms.FileField(required=False)

class BlastForm(forms.Form):

    # sequence_query = forms.CharField(widget=forms.Textarea, required=False, help_text='Sequence in FASTA format.')

    show_all = forms.BooleanField(required=False, label='Show all?')
    file_field = forms.FileField(required=True, help_text='File of fasta sequences.')

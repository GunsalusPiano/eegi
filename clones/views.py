from django.shortcuts import render, get_object_or_404
from django.core import serializers
# from clones.forms import CloneSearchForm, GeneSearchForm, GeneSearchFileFieldForm
from clones.forms import CloneSearchForm, GeneSearchForm
from clones.models import Clone, Gene, CloneTarget
from library.models import LibraryStock
from utils.pagination import get_paginated
import json

CLONES_PER_PAGE = 20


def clones(request):
    """Render the page listing all RNAi clones."""
    if 'clone_query' in request.GET:
        form = CloneSearchForm(request.GET)

        if form.is_valid():
            data = form.cleaned_data
            clones = data['clone_query']
        else:
            clones = []

    else:
        form = CloneSearchForm()
        clones = Clone.objects.all()

    display_clones = get_paginated(request, clones, CLONES_PER_PAGE)

    context = {
        'clones': clones,
        'display_clones': display_clones,
        'form': form,
    }

    return render(request, 'clones.html', context)


def clone(request, id):
    """Render the page to view a single RNAi clone."""
    clone = get_object_or_404(Clone, pk=id)

    context = {
        'clone': clone,
    }

    return render(request, 'clone.html', context)

def descriptions(request):

    j = ''
    query = []
    genes = ''
    clone_targets = ''
    stocks = ''

    if request.method == 'POST':

        form = GeneSearchForm(request.POST, request.FILES)

        if request.FILES:
            query = request.FILES['file_field'].read().split()
        else:
            query.append(request.POST['gene_query'])


        j = render_table(request.POST['choice_field'], query)

    else:
        form = GeneSearchForm(initial={'choice_field':'wb_gene_id'})

    context = {
        'data':j,
        'form':form,
    }

    return render(request, 'descriptions.html', context)


def render_table(choice_field, query):

    d = []

    if choice_field == 'wb_gene_id':
        genes = Gene.objects.filter(id__in=query)
        clone_targets = CloneTarget.objects.filter(gene__in=genes.values('id'))
        stocks = LibraryStock.objects.filter(intended_clone__in = clone_targets.values('clone'))

    elif choice_field == 'locus':
        genes = Gene.objects.filter(locus__in=query)
        clone_targets = CloneTarget.objects.filter(gene__in=genes.values('id'))
        stocks = LibraryStock.objects.filter(intended_clone__in = clone_targets.values('clone'))

    elif choice_field == 'clone_id':
        clone_targets = CloneTarget.objects.filter(clone__in=query)
        genes = Gene.objects.filter(id__in=clone_targets.values('gene'))
        stocks = LibraryStock.objects.filter(intended_clone__in=clone_targets.values('clone'))

    else:
        stocks = LibraryStock.objects.filter(id__in=query)
        clone_targets = CloneTarget.objects.filter(clone__in=stocks.values('intended_clone'))
        genes = Gene.objects.filter(id__in=clone_targets.values('gene'))

    for gene in genes:
        row = [ \
            '<a href="'+gene.get_wormbase_url()+'">'+gene.id+'</a>', \
            gene.cosmid_id, \
            gene.locus, \
            gene.gene_type, \
            gene.gene_class_description, \
            gene.functional_description.replace("'","")]

        if clone_targets.filter(gene=gene).exists():

            for clone_target in clone_targets.filter(gene=gene):
                stockStr = ""
                for stock in stocks.filter(intended_clone=clone_target.clone):
                    stockStr += stock.id+',\n'
                row.extend((
                    clone_target.clone_id,\
                    clone_target.transcript_isoform,\
                    stockStr))
        else:
            row.extend(("","",""))
        d.append(row)


    return json.dumps(d)

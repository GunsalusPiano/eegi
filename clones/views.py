from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.conf import settings
from clones.forms import CloneSearchForm, GeneSearchForm, BlastForm
from clones.models import Clone, Gene, CloneTarget
from library.models import LibraryStock
from utils.pagination import get_paginated
import json
from subprocess import Popen, PIPE
from time import sleep
import os

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

def blast(request):

    """
    This method runs blast locally on a user uploaded fasta file.
    it searches the WS260 version of the C. elegans genome with each query
    and then runs the ouput against its gff annotation file.
    """

    #TODO: Make a management script that downloads a specific version of this
    # and updates it.

    data = ''
    query = ''
    j = []
    if request.method == 'POST':
        form = BlastForm(request.POST, request.FILES)

        if request.FILES:
            query = request.FILES['file_field'].read()
	    with open('/home/eegi/.django-tmp/blah', 'w') as f:
		f.write(query)
            """
            This is handled by TemporaryFileUploadHandler, which writes to disk
            and is assigned a randomly generated filepath. The uploader is defined
            in settings.py
            """

            # runs blast on local server
            blast_out, blast_err = Popen([
                '/home/eegi/software/ncbi-blast-2.6.0+/bin/blastn',
		'-query','/home/eegi/.django-tmp/blah',
		'-db', '/home/eegi/django-files/c_elegans_blast_db/c_elegans.PRJNA13758.WS260.genomic.fa',
                '-outfmt','6',
                '-max_target_seqs','1',
                '-culling_limit','1',
                '-num_threads','4',
                '-evalue','0.00005'],
                stdout=PIPE,
                stderr=PIPE,
            ).communicate()

            for hit in blast_out.rstrip().split('\n'):
                hit = hit.split('\t')
                region = hit[1]+':'+hit[8]+'-'+hit[9]
                tabix_out, tabix_err = Popen([
                    '/home/lg/code/build/bin/tabix',
                    '/home/eegi/django-files/c_elegans_blast_db/c_elegans.PRJNA13758.WS260.annotations.sorted.gff2.gz',
		     region],
                    stdout=PIPE,
                    stderr=PIPE
                ).communicate()

                for tabix in tabix_out.rstrip().split('\n'):
                    if tabix:
                        tabix = tabix.split('\t')
                        l = []
                        l.extend((
                            hit[0],   # query name
                            hit[1],   # subject name
                            tabix[1], # source i.e. blastx, gene
                            tabix[2], # method, i.e. cds
                            tabix[3], # start position
                            tabix[4], # stop position
                            tabix[8]  # features
                        ))
                        j.append(l)
            data = json.dumps(j)


    else:
        form = BlastForm()

    context = {
        'data':data,
        'form':form,
    }

    return render(request, 'blast.html', context)

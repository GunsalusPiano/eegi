import argparse
import csv

from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from clones.models import Gene
from utils.scripting import require_db_write_acknowledgement
from django.conf import settings


class Command(BaseCommand):
    """
    Command to add WormBase gene functional descriptions.

    The WormBase file can be found at:

        ftp://ftp.wormbase.org/pub/wormbase/releases/WSX/species/c_elegans/
        PRJNA13758/annotation/
        c_elegans.PRJNA13758.WSX.functional_descriptions.txt.gz

    where WSX should be replaced with the desired WormBase version.

    As of November 2015, Firoz's mapping database uses WS240, so Katherine
    also used WS240 for the functional descriptions.
    """

    help = 'Import gene functional descriptions.'

    def add_arguments(self, parser):
        parser.add_argument('file', type=argparse.FileType('r'),
                            help="WormBase functional descriptions file. "
                                 "See this command's docstring "
                                 "for more details.")

    def handle(self, **options):
        f = options['file']

        require_db_write_acknowledgement()

        descriptions = _parse_wormbase_file(f)

        genes = Gene.objects.all()

        num_mismatches = 0
        for gene in genes:
            if gene.id not in descriptions:
                raise CommandError('{} not found in WormBase file'
                                   .format(gene))
            info = descriptions[gene.id]

            # Sanity check: Does WormBase molecular_name match the
            # cosmid_id in Firoz's database?
            wb_molecular = info['molecular_name']
            firoz_cosmid = gene.cosmid_id
            if (not wb_molecular.startswith(firoz_cosmid)):
                num_mismatches += 1
                self.stderr.write('Molecular/cosmid mismatch for {}: '
                                  'WormBase says {}, Firoz says {}'
                                  .format(gene, wb_molecular, firoz_cosmid))

            # Sanity check: Does WormBase public_name match the
            # locus in Firoz's database?
            wb_public = info['public_name']
            firoz_locus = gene.locus
            if (wb_public != firoz_locus and
                    not (firoz_locus == '' and wb_public == firoz_cosmid)):
                num_mismatches += 1
                self.stderr.write('Public/locus mismatch for {}: '
                                  'WormBase says {}, Firoz says {}'
                                  .format(gene, wb_public, firoz_locus))

            gene.functional_description = info['concise_description']
            gene.gene_class_description = info['gene_class_description']
            del descriptions[gene.id]
            gene.save()

        if num_mismatches:
            self.stderr.write('Total number mismatches: {}'
                              .format(num_mismatches))

        for description in descriptions.keys():
            gene = Gene.objects.get_or_create(id=description,
                                cosmid_id=descriptions[description]['molecular_name'],
                                locus=descriptions[description]['public_name'],
                                gene_type="",
                                gene_class_description=descriptions[description]['gene_class_description'],
                                functional_description=descriptions[description]['concise_description'])

            gene.save()
        _genes_to_json()


"""
Writes wormbase files to JSON document for faster rendering.
"""
def _genes_to_json():
    descritptions = Gene.objects.all()
    json = serializers.serialize('json', descritptions)

    with open(settings.BASE_DIR+'/website/static/wbm_gene_descs.json', 'w') as f:
        f.write(json)


def _parse_wormbase_file(f):
    # Skip header
    while True:
        row = next(f)
        if row[0] != '#':
            break

    fieldnames = row
    fieldnames = fieldnames.split()

    reader = csv.reader(f, delimiter='\t')

    d = {}
    for row in reader:
        gene_id = row[0]
        d[gene_id] = {}
        for k, v in zip(fieldnames[1:], row[1:]):
            d[gene_id][k] = v

    return d

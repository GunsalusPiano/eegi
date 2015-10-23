import os
from collections import OrderedDict

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404

from eegi.settings import MATERIALS_DIR
from experiments.models import Experiment
from experiments.forms import ExperimentFilterForm
from library.models import LibraryWell, LibraryPlate
from utils.well_tile_conversion import tile_to_well
from utils.http import http_response_ok
from worms.models import WormStrain


EXPERIMENTS_PER_PAGE = 100


def experiment_plates(request, context=None):
    """Render the page to search for experiment plates."""
    experiments = None
    display_experiments = None

    if len(request.GET):
        form = ExperimentFilterForm(request.GET)
        if form.is_valid():
            experiments = form.cleaned_data['experiments']

            paginator = Paginator(experiments, EXPERIMENTS_PER_PAGE)
            page = request.GET.get('page')
            try:
                display_experiments = paginator.page(page)
            except PageNotAnInteger:
                display_experiments = paginator.page(1)
            except EmptyPage:
                display_experiments = paginator.page(paginator.num_pages)

    else:
        form = ExperimentFilterForm()

    context = {
        'form': form,
        'experiments': experiments,
        'display_experiments': display_experiments,
    }

    return render(request, 'experiment_plates.html', context)


def experiment_plates_grid(request, screen_stage):
    """Render the page showing all experiments as a grid."""
    worms = WormStrain.objects.all()
    experiments = (Experiment.objects
                   .filter(screen_stage=screen_stage, is_junk=False)
                   .select_related('library_plate', 'worm_strain'))

    plate_pks = (experiments.order_by('library_plate')
                 .values_list('library_plate', flat=True)
                 .distinct())
    plates = LibraryPlate.objects.filter(pk__in=plate_pks)

    header = []
    for worm in worms:
        if worm.permissive_temperature:
            header.append((worm, worm.permissive_temperature))
        if worm.restrictive_temperature:
            header.append((worm, worm.restrictive_temperature))

    e = OrderedDict()
    for plate in plates:
        e[plate] = OrderedDict()
        for worm in worms:
            if worm not in e[plate]:
                e[plate][worm] = OrderedDict()
            if worm.permissive_temperature:
                e[plate][worm][worm.permissive_temperature] = []
            if worm.restrictive_temperature:
                e[plate][worm][worm.restrictive_temperature] = []

    for experiment in experiments:
        plate = experiment.library_plate
        worm = experiment.worm_strain
        temp = experiment.temperature

        if temp in e[plate][worm]:
            e[plate][worm][temp].append(experiment)

    context = {
        'screen_stage': screen_stage,
        'header': header,
        'e': e,
    }

    return render(request, 'experiment_plates_grid.html', context)


def experiment_plates_vertical(request, ids):
    """Render the page to view vertical images of one or more experiments."""
    ids = ids.split(',')
    experiments = []
    for id in ids:
        experiment = get_object_or_404(Experiment, pk=id)
        experiment.library_wells = LibraryWell.objects.filter(
            plate=experiment.library_plate).order_by('well')
        experiments.append(experiment)

    context = {
        'experiments': experiments,

        # Default to thumbnail
        'mode': request.GET.get('mode', 'thumbnail')
    }

    return render(request, 'experiment_plates_vertical.html', context)


def experiment_plate(request, id):
    """Render the page to see a particular experiment plate."""
    experiment = get_object_or_404(Experiment, pk=id)

    library_wells = LibraryWell.objects.filter(
        plate=experiment.library_plate).order_by('well')

    # Add row attribute in order to use regroup template tag
    for library_well in library_wells:
        library_well.row = library_well.get_row()

    context = {
        'experiment': experiment,
        'library_wells': library_wells,

        # Default to thumbnail
        'mode': request.GET.get('mode', 'thumbnail'),
    }

    return render(request, 'experiment_plate.html', context)


def experiment_well(request, id, well):
    """Render the page to see a particular experiment well."""
    experiment = get_object_or_404(Experiment, pk=id)

    library_well = LibraryWell.objects.filter(
        plate=experiment.library_plate).filter(well=well)[0]

    devstar_url = experiment.get_image_url(well, mode='devstar')
    devstar_available = http_response_ok(devstar_url)

    context = {
        'experiment': experiment,
        'well': well,
        'library_well': library_well,
        'devstar_available': devstar_available,

        # Default to full-size images
        'mode': request.GET.get('mode', 'big')
    }

    return render(request, 'experiment_well.html', context)


BEFORE_AND_AFTER_DIR = MATERIALS_DIR + '/before_and_after/categories'
BEFORE_AND_AFTER_PER_PAGE = 10


def before_and_after_category(request, category):
    tuples = []

    f = open(BEFORE_AND_AFTER_DIR + '/' + category, 'r')
    rows = f.readlines()
    for row in rows:
        experiment_id, tile = row.split('_')
        experiment = get_object_or_404(Experiment, pk=experiment_id)
        tile = tile.split('.bmp')[0]
        well = tile_to_well(tile)
        tuples.append((experiment, well, tile))
    f.close()

    paginator = Paginator(tuples, BEFORE_AND_AFTER_PER_PAGE)
    page = request.GET.get('page')

    try:
        display_tuples = paginator.page(page)
    except PageNotAnInteger:
        display_tuples = paginator.page(1)
    except EmptyPage:
        display_tuples = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'tuples': tuples,
        'display_tuples': display_tuples,
    }

    return render(request, 'before_and_after_category.html', context)


def before_and_after_categories(request):
    categories = os.listdir(BEFORE_AND_AFTER_DIR)

    context = {
        'categories': categories,
    }

    return render(request, 'before_and_after_categories.html', context)

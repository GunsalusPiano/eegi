from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from clones.models import Clone
from experiments.forms import RNAiKnockdownForm, MutantKnockdownForm
from experiments.models import Experiment
from library.models import LibraryWell, LibraryPlate
from worms.models import WormStrain


def rnai_knockdown(request, clone, temperature):
    """Render the page displaying control worms (N2) with an RNAi knockdown."""
    clone = get_object_or_404(Clone, pk=clone)
    n2 = get_object_or_404(WormStrain, pk='N2')
    library_wells = (LibraryWell.objects
                     .filter(intended_clone=clone,
                             plate__screen_stage__gt=0)
                     .order_by('-plate__screen_stage'))

    # Each element of 'data' is in format (as needed by the template):
    #   (library_well, (experiments_ordered_by_id))
    data = []
    for library_well in library_wells:
        experiments = (Experiment.objects
                       .filter(is_junk=False, worm_strain=n2,
                               temperature=temperature,
                               library_plate=library_well.plate)
                       .order_by('-id'))
        if experiments:
            data.append((library_well, experiments))

    context = {
        'clone': clone,
        'temperature': temperature,
        'data': data,
    }

    return render(request, 'rnai_knockdown.html', context)


def mutant_knockdown(request, worm, temperature):
    """Render the page displaying control bacteria (L4440) with a mutant
    knockdown."""
    l4440 = get_object_or_404(Clone, pk='L4440')
    worm = get_object_or_404(WormStrain, pk=worm)
    plates = LibraryPlate.objects.filter(screen_stage__gt=0)

    # Each element of 'data' is in format (as needed by the template):
    #   (experiment, l4440_wells)
    data = []
    for plate in plates:
        l4440_wells = plate.wells.filter(intended_clone=l4440)
        if l4440_wells:
            experiments = (Experiment.objects
                           .filter(is_junk=False, worm_strain=worm,
                                   temperature=temperature,
                                   library_plate=plate)
                           .order_by('id'))
            for experiment in experiments:
                data.append((experiment, l4440_wells))

    data.sort(key=lambda x: x[0].id)

    context = {
        'worm': worm,
        'temperature': temperature,
        'data': data,
    }

    return render(request, 'mutant_knockdown.html', context)


def single_knockdown_search(request):
    """Render the page to search for a single knockdown."""
    error = ''
    if request.method == 'POST':
        if 'rnai' in request.POST:
            mutant_form = MutantKnockdownForm(prefix='mutant',
                                              initial={'screen': 'SUP'})
            rnai_form = RNAiKnockdownForm(request.POST, prefix='rnai')
            if rnai_form.is_valid():
                try:
                    data = rnai_form.cleaned_data
                    target = data['target']
                    temperature = data['temperature']

                    try:
                        clone = Clone.objects.get(pk=target)
                    except ObjectDoesNotExist:
                        raise ObjectDoesNotExist('No clone matches target.')

                    return redirect(rnai_knockdown, clone, temperature)

                except Exception as e:
                    error = e.message

        elif 'mutant' in request.POST:
            rnai_form = RNAiKnockdownForm(prefix='rnai')
            mutant_form = MutantKnockdownForm(request.POST, prefix='mutant')
            if mutant_form.is_valid():
                try:
                    data = mutant_form.cleaned_data
                    query = data['query']
                    screen = data['screen']

                    if screen != 'ENH' and screen != 'SUP':
                        raise Exception('screen must be ENH or SUP')

                    if screen == 'ENH':
                        worms = (WormStrain.objects
                                 .filter(Q(gene=query) | Q(allele=query) |
                                         Q(id=query))
                                 .exclude(permissive_temperature__isnull=True))
                    else:
                        worms = (WormStrain.objects
                                 .filter(Q(gene=query) | Q(allele=query) |
                                         Q(id=query))
                                 .exclude(
                                     restrictive_temperature__isnull=True))

                    if len(worms) == 0:
                        raise Exception('No worm strain matches query.')
                    elif len(worms) > 1:
                        raise Exception('Multiple worm strains match query.')
                    else:
                        worm = worms[0]

                    if screen == 'ENH':
                        temperature = worm.permissive_temperature
                    else:
                        temperature = worm.restrictive_temperature
                        return redirect(mutant_knockdown, worm, temperature)

                except Exception as e:
                    error = e.message

    else:
        rnai_form = RNAiKnockdownForm(prefix='rnai')
        mutant_form = MutantKnockdownForm(prefix='mutant',
                                          initial={'screen': 'SUP'})

    context = {
        'rnai_form': rnai_form,
        'mutant_form': mutant_form,
        'error': error,
    }

    return render(request, 'single_knockdown_search.html', context)
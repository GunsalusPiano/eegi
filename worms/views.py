from django.shortcuts import render, redirect
from django.contrib import messages
from worms.models import WormStrain
from django.forms import ModelForm
from worms.forms import AddStrain
from django.contrib.auth.decorators import login_required, permission_required


def worms(request):
    """Render the page listing all worm strains used in the screen."""
    worms = WormStrain.objects.all()
    context = {'worms': worms}
    return render(request, 'worms.html', context)


@login_required
def add_strain(request):

    if request.method == 'POST':
        form = AddStrain(request.POST)

        if form.is_valid():
            # strain = form.cleaned_data['strain']
            # gene = form.cleaned_data['gene']
            # allele = form.cleaned_data['allele']
            # genotype = form.cleaned_data['genotype']
            # permissive = form.cleaned_data['permissive']
            # restrictive = form.cleaned_data['restrictive']

            form.save()
            # form = AddPlasmid()
            messages.success(request, 'Created Worm Strain!')

            return redirect('add_strain_url')
    else:
        form = AddStrain()

    context = {
        'form':form,
    }
    return render(request, 'add_strain.html', context)

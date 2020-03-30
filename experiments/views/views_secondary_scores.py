from __future__ import division
from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from experiments.forms import SecondaryScoresForm, ScreenSummaryForm

from experiments.helpers.scores import get_average_score_weight, calculate_average_scores

from worms.models import WormStrain

from chartit import DataPool, Chart

NOAH_ID = 14
MALCOLM_ID = 22
KATHERINE_ID = 1
SHERLY_ID = 4
GISELLE_ID = 3

IDS = [NOAH_ID, MALCOLM_ID, SHERLY_ID]

def screen_summary(request, screen_stage, reagent, assay, interesting):
    """
    Inteface for searching for and exporting screen results in table format

    """

    if request.GET:
        form = ScreenSummaryForm(request.GET)

        if form.is_valid():

            screen_type = form.cleaned_data['screen_type']
            screen_stage = form.cleaned_data['screen_stage']
            gene = form.cleaned_data['gene']

            context = {
                'screen_stage': screen_stage,
                'screen_type': screen_type,
                'gene': gene,
            }
            
            return render(request, 'screen_summary.html', context)


# def secondary_scores(request, worm, worm2, temperature, username=None):
def secondary_scores(request, worm, temperature, worm2=None, username=None):
    """
    Render the page to display secondary scores for a mutant/screen.

    Results show strongest positives on top.
    """
    worm = get_object_or_404(WormStrain, pk=worm)
    if worm2:
        worm2 = get_object_or_404(WormStrain, pk=worm2)

    try:
        screen_type = worm.get_screen_type(temperature)
    except Exception:
        raise Http404

    if username:
        user = get_object_or_404(get_user_model(), username=username)
        data = worm.get_organized_scores(screen_type, screen_stage=2,
                                         most_relevant_only=True,
                                         scorer=user)
        if worm2:
            data2 = worm2.get_organized_scores(screen_type, screen_stage=2,
                                         most_relevant_only=True,
                                         scorer=user)

    else:
        data = worm.get_organized_scores(screen_type, screen_stage=2,
                                         most_relevant_only=True,
                                         scorer_id__in=IDS)
        if worm2:
            data2 = worm2.get_organized_scores(screen_type, screen_stage=2,
                                         most_relevant_only=True,
                                         scorer_id__in=IDS)

    data_stats = calculate_average_scores(data)
    if worm2:
        data2_stats = calculate_average_scores(data2)

    data = OrderedDict(sorted(
        data.iteritems(),
        key=lambda x: (x[0].passes_stringent,
                       x[0].passes_percent,
                       x[0].passes_count,
                       x[0].avg),
        reverse=True))

    data2_scores = OrderedDict()
    if worm2:
        for stock, expts in data.iteritems():
            if stock in data2:
                data2_scores[stock] = data2[stock]
            else:
                data2_scores[stock] = ""

    context = {
        'worm': worm,
        'screen_type': screen_type,
        'temperature': temperature,
        'data': data,
        'num_passes_percent': data_stats['num_passes_percent'],
        'num_passes_count': data_stats['num_passes_count'],
        'num_passes_stringent': data_stats['num_passes_stringent'],
        'num_experiment_columns': data_stats['num_experiment_columns'],
        'data2_scores': data2_scores,
    }

    return render(request, 'secondary_scores.html', context)

def find_secondary_scores(request):
    """Render the page to find secondary scores for a mutant/screen."""
    if request.method == 'POST':
        form = SecondaryScoresForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            worm = data['worm']
            temperature = data['temperature']
            if data['worm2']:
                worm2 = data['worm2']
                return redirect(secondary_scores, worm.pk, temperature, worm2.pk)
            else:
                return redirect(secondary_scores, worm.pk, temperature)

    else:
        form = SecondaryScoresForm(initial={'screen_type': 'SUP'})

    context = {
        'form': form,
    }

    return render(request, 'find_secondary_scores.html', context)

def plot_secondary_scores(request,worm,temperature):
        """
        Render the page to plot secondary scores for a mutant/screen.
        """

        worm = get_object_or_404(WormStrain, pk=worm)

        try:
            screen_type = worm.get_screen_type(temperature)
        except Exception:
            raise Http404

        data = worm.get_organized_scores(screen_type, screen_stage=2)

        lstock_data = list()
        exp_data = list()

        for lstock,experiment in data.iteritems():
            # print lstock
            count = 0
            for k,v in experiment.items():
                # print k
                count += 1
            # chart_data.append([lstock.get_display_string(),count])
            lstock_data.append("'"+lstock.get_display_string()+"'")
            exp_data.append(str(count))

        lstock_data = ','.join(lstock_data)
        exp_data = ','.join(exp_data)


        exp_chart="""
            $(document).ready(function(){
                $('#exp_chart').highcharts({
                    chart:{
                        type: 'column'
                    },
                    title:{
                        text: 'Replicates Scored per Gene'
                    },
                    xAxis:{
                        categories:["""+lstock_data+"""]
                    },
                    yAxis:{
                        title: {
                            text: '# of Assays Scored'
                        }
                    },
                    plotOptions: {
                        series: {
                            allowPointSelect: true,
                            marker: {
                                states: {
                                    select: {
                                        fillColor: 'red',
                                        lineWidth: 5
                                    }
                                }
                            }
                        }
                    },
                    series:[{
                        name:'Assays',
                        data:["""+exp_data+"""]
                    }]
                });
            });

        """


        context = {
            'worm': worm,
            'screen_type': screen_type,
            'temperature': temperature,
            'data': data,
            'exp_chart':exp_chart,
            # 'chart':chart,
        }

        return render(request, 'plot_secondary_scores.html', context)

def find_plot_secondary_scores(request):
    """Render the page to find secondary scores for a mutant/screen for plotting."""
    if request.method == 'POST':
        form = SecondaryScoresForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            worm = data['worm']
            temperature = data['temperature']
            return redirect(plot_secondary_scores, worm.pk, temperature)

    else:
        form = SecondaryScoresForm(initial={'screen_type': 'SUP'})

    context = {
        'form': form,
    }

    return render(request, 'find_plot_secondary_scores.html', context)

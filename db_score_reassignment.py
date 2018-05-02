# query to remove 47-49 from non-N2 control
# delete record from ManualScore record join Experiment on experiment_id = Experiment.id where timestamp >= '2018-04-01' and worm_strain_id != 'N2' and `score_code_id` in (47, 48, 49, 20)

# query to get IDs for 50-53
# It seems the first entry of a new score (47-53) is on 2-13-2018, so that will be my cutoff
# select experiment_id,score_code_id,timestamp from ManualScore record join Experiment on experiment_id = Experiment.id where timestamp >= '2018-03-01' and `score_code_id` between 50 and 53;

# ID = dict with exp id as key, score code ID and timestamp as values

# ManualScore.objects.filter()

ids = dict()
with open('query_result.csv', 'r') as f:
    for line in f.readlines():
        line = line.rstrip().split(',')
        ids[line[0]] = dict()
        ids[line[0]]['score'] = int(line[1])
        ids[line[0]]['time'] = line[2]

for id in ids:
    if ids[id]['score'] != 53:
        for control in Experiment.objects.get(id=id).get_link_to_exact_n2_control():
            # print(control)
            control_score = ManualScore(experiment=control, score_code=ManualScoreCode.objects.get(id=ids[id]['score']),scorer=User.objects.get(id=14), timestamp=ids[id]['time'])
            control_score.save()
        manual_scores = ManualScore.objects.filter(experiment=id,score_code=ManualScoreCode.objects.get(id=ids[id]['score']),scorer=User.objects.get(id=14))
        if len(manual_scores) > 1:
            timestamp = manual_scores.values('timestamp')[0]
            ManualScore.objects.filter(experiment=id,scorer=User.objects.get(id=14),timestamp=timestamp['timestamp']).delete()
        ManualScore.objects.get(experiment=id,score_code=ManualScoreCode.objects.get(id=ids[id]['score']),scorer=User.objects.get(id=14)).delete()

control_score = ManualScore(experiment=control, score_code=ManualScoreCode.objects.get(id=53),scorer=User.objects.get(id=14), timestamp='2018-04-23 18:36:18.916485')

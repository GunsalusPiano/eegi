from django.test import TestCase
from experiments.forms import FilterExperimentWellsToScoreForm
from experiments.models import Experiment, ExperimentPlate
from worms.tests.base import WormTestCase

# Create your tests here.

#####################
# Experiment Plates #
#####################
class ExperimentPlateTestCase(TestCase):

    def setUp(self):
        for i in range(1,9):
            ExperimentPlate.objects.create(
                id=i, screen_stage=2,temperature=22.5, date="2015-09-25"
            )

    def get_experiment_plates(self):
        plates=dict()
        for i in range(1,9):
            plates[i]=ExperimentPlate.objects.get(id=i)
        return plates

####################
# Experiment wells #
####################
class ExperimentTestCase(ExperimentPlateTestCase):
    def setUp(self):

        plates = self.get_experiment_plates()
        n2, dnc1, glp1, emb8 = self.get_worms()

        for i in range(1,9):

            Experiment.objects.create(
                id=i, plate=plates[i], well="A01",
                worm_strain=emb8, library_stock="test_stock"
            )

    # def get_experiments(self):
    #     exps = []
    #     for i in range(1,9):
    #         print i

# class ExperimentModelTestCase(ExperimentTestCase):
#     # def test_get_row(self):
#     def test_get_experiments(self):
#         self.get_experiments()


class TestForm(TestCase):

    def testform_data(self):

        form_data={
            # LEVELS is for enhancer, since it's scored with LEVELS
            # of a particular phenotype
            'score_form_key':"LEVELS",
            'unscored_by_user': True,
            'randomize_order': True,
            'score_only_4_reps': True,
            'exclude_l4440': True,
            'exclude_no_clone': True,
            'images_per_page': 10
        }

        form = FilterExperimentWellsToScoreForm(form_data)
        print form
        self.assertTrue(form.is_valid())
        return form

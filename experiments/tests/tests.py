from django.test import TestCase
from django.contrib.auth.models import User
from experiments.forms import FilterExperimentWellsToScoreForm
from experiments.models import Experiment, ExperimentPlate, ManualScoreCode, ManualScore
from worms.tests.base import WormTestCase
from worms.models import WormStrain

# Create your tests here.

###################################################
# IMPORTANT: tests methods MUST start with 'test' #
###################################################

##############
# Test Users #
##############
class UserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username="Test",
            password="blah"
        )

    def test_user(self):
        pass
#####################
# Experiment Plates #
#####################
class ExperimentPlateTestCase(TestCase):
    # Creating mock experiment plates with a unique plate ID
    # These will be used for replicates
    @classmethod
    def setUpTestData(cls):
        for i in range(1,9):
            ExperimentPlate.objects.create(
                id=i, screen_stage=2,temperature=22.5, date="2015-09-25"
            )
        cls.plates = ExperimentPlate.objects.all()

    def test_print_experiment_plates(self):
        pass

####################
# Experiment wells #
####################

class ExperimentTestCase(ExperimentPlateTestCase):
    # Setting up the actual experiments, making 8 replicates
    # across the 8 mock plates.
    @classmethod
    def setUpTestData(cls):
        # Need to call this in order to inherit parent database
        # There is a teardown command issued at the end of it.

        ExperimentPlateTestCase.setUpTestData()
        WormTestCase.setUpTestData()

        # n2, dnc1, glp1, emb8 = super(ExperimentTestCase,cls).get_worms()
        # print n2
        # for i in range(1,9):
        #
        #     Experiment.objects.create(
        #         id=i, plate=Experiment.objects.filter(pk=i), well="A01",
        #         worm_strain=emb8, library_stock="test_stock"
        #     )
        # cls.experiments = Experiment.object.all()

    #
    # def test_worm_strain(self):
    #     print self.get_worms()
    #
    # def test_print_experiments(self):
    #     print self.experiments
    #
    # def test_get_experiments(self):
    #     return self.experiments

"""
######################
# Manual Score Codes #
######################
class ManualScoreCodeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        ManualScoreCode.object.create(
            id=1,
            description="unscored"
        )

#################
# Manual Scores #
#################
class ManualScoreTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        experiments = cls.get_experiments()
        for e in experiments:
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.objects.filter(descritpion="unscored"),
                scorer=User.objects.filter(username="Test")
            )
    #
    # def print_manual_scores(self):
    #


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
        self.assertTrue(form.is_valid())
        query = form.process()
"""

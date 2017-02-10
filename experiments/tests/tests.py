from django.test import TestCase
from django.contrib.auth.models import User
from experiments.forms import FilterExperimentWellsToScoreForm
from experiments.models import Experiment, ExperimentPlate, ManualScoreCode, ManualScore
from worms.tests.base import WormTestCase
from worms.models import WormStrain
from library.models import LibraryPlate, LibraryStock

# Create your tests here.

###################################################
# IMPORTANT: tests methods MUST start with 'test' #
# in order to be implicitly executed.             #
###################################################


##############
# Test Users #
##############
class UserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username="Test"
        )

    def test_username(self):
        self.assertEquals(self.user.get_username(),"Test")

class LibraryPlateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        LibraryPlate.objects.create(
            id="library_plate_1",
            number_of_wells=96,
            screen_stage=2
        )

        cls.library_plate = LibraryPlate.objects.all()

    def test_library_plate(self):
        pass

class LibraryStockTestCase(LibraryPlateTestCase):
    @classmethod
    def setUpTestData(cls):
        super(LibraryStockTestCase,cls).setUpTestData()

        LibraryStock.objects.create(
            id="library_stock_1",
            plate=cls.library_plate.get(id="library_plate_1"),
            well="A01",
        )

        cls.library_stock = LibraryStock.objects.all()

    def test_library_stock(self):
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

class ExperimentTestCase(ExperimentPlateTestCase, WormTestCase, LibraryStockTestCase):
    # Setting up the actual experiments, making 8 replicates
    # across the 8 mock plates.
    @classmethod
    def setUpTestData(cls):
        # Need to call this in order to inherit parent database
        # There is a teardown command issued at the end of it.
        super(ExperimentTestCase,cls).setUpTestData()

        # initializing the worm db
        WormTestCase.setUpTestData()

        LibraryStockTestCase.setUpTestData()

        # n2, dnc1, glp1, emb8 = super(ExperimentTestCase,cls).get_worms()
        # print n2

        plate = {1:"A",
                 2:"B",
                 3:"C",
                 4:"D",
                 5:"E",
                 6:"F",
                 7:"G",
                 8:"H"}

        for i in range(1,9):

            Experiment.objects.create(
                id=str(i)+"_"+plate[i]+"01", plate=cls.plates.get(pk=i), well=plate[i]+"01",
                worm_strain=WormTestCase.worms.get(id='MJ69'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored four times."
            )

            Experiment.objects.create(
                id=str(i+8)+"_"+plate[i]+"02", plate=cls.plates.get(pk=i), well=plate[i]+"02",
                worm_strain=WormTestCase.worms.get(id='N2'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are not scored at all."
            )

            Experiment.objects.create(
                id=str(i+16)+"_"+plate[i]+"03", plate=cls.plates.get(pk=i), well=plate[i]+"03",
                worm_strain=WormTestCase.worms.get(id='EU552'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored once."
            )

            Experiment.objects.create(
                id=str(i+24)+"_"+plate[i]+"04", plate=cls.plates.get(pk=i), well=plate[i]+"04",
                worm_strain=WormTestCase.worms.get(id='EU1006'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored all 8 times."
            )

        cls.experiments = Experiment.objects.all()
        # print cls.experiments

    def test_experiment(self):
        pass



######################
# Manual Score Codes #
######################
class ManualScoreCodeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        ManualScoreCode.objects.create(
            id=1,
            description="unscored"
        )

        cls.manual_score_codes = ManualScoreCode.objects.all()

    def test_manual_score_code(self):
        pass

#################
# Manual Scores #
#################
class ManualScoreTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        ExperimentTestCase.setUpTestData()
        ManualScoreCodeTestCase.setUpTestData()
        UserTestCase.setUpTestData()

        # Score only 4 MJ69
        for e in ExperimentTestCase.experiments.filter(worm_strain="MJ69")[:4]:
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.manual_score_codes.get(description="unscored"),
                scorer=User.objects.get(username="Test")
            )

        # Score all 8 EU1006
        for e in ExperimentTestCase.experiments.filter(worm_strain="EU1006"):
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.manual_score_codes.get(description="unscored"),
                scorer=User.objects.get(username="Test")
            )

        # Score only 1 EU552
        for e in ExperimentTestCase.experiments.filter(worm_strain="EU552")[:1]:
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.manual_score_codes.get(description="unscored"),
                scorer=User.objects.get(username="Test")
            )

        cls.manual_scores = ManualScore.objects.all()

    def test_manual_score(self):
        pass


################################################
# Example Input Form to Filter Images to Score #
################################################
class FilterExperimentWellsToScoreFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):

        ManualScoreTestCase.setUpTestData()

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

        cls.form = FilterExperimentWellsToScoreForm(form_data)

        # cls.assertTrue(form.is_valid())
        # query = form.process()

    def test_filter_experiment_wells_to_score_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_score_only_4_reps(self):
        self.assertTrue(self.form.cleaned_data['score_only_4_reps'])

        print ManualScoreTestCase.manual_scores.filter(
            experiment__in=ExperimentTestCase.experiments,
            experiment__is_junk=False,
            scorer=UserTestCase.user).values('experiment')

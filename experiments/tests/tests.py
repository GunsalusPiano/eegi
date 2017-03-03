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

        for i in range(1,9):

            Experiment.objects.create(
                id=str(i)+"_"+"A01", plate=cls.plates.get(pk=i), well="A01",
                worm_strain=WormTestCase.worms.get(id='MJ69'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored four times."
            )

            Experiment.objects.create(
                id=str(i+8)+"_"+"A02", plate=cls.plates.get(pk=i), well="A02",
                worm_strain=WormTestCase.worms.get(id='N2'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are not scored at all."
            )

            Experiment.objects.create(
                id=str(i+16)+"_"+"A03", plate=cls.plates.get(pk=i), well="A03",
                worm_strain=WormTestCase.worms.get(id='EU552'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored once."
            )

            Experiment.objects.create(
                id=str(i+24)+"_"+"A04", plate=cls.plates.get(pk=i), well="A04",
                worm_strain=WormTestCase.worms.get(id='EU1006'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored all 8 times."
            )

            Experiment.objects.create(
                id=str(i+32)+"_"+"A05", plate=cls.plates.get(pk=i), well="A05",
                worm_strain=WormTestCase.worms.get(id='EU1006'),
                library_stock=LibraryStockTestCase.library_stock.get(id="library_stock_1"),
                comment="These are scored 6 times."
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

        # Score only 4 A01
        for e in ExperimentTestCase.experiments.filter(well="A01")[:4]:
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.manual_score_codes.get(description="unscored"),
                scorer=User.objects.get(username="Test")
            )

        # A02 isn't scored at all

        # Score only 1 A03
        for e in ExperimentTestCase.experiments.filter(well="A03")[:1]:
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.manual_score_codes.get(description="unscored"),
                scorer=User.objects.get(username="Test")
            )

        # Score all 8 A04
        for e in ExperimentTestCase.experiments.filter(well="A04"):
            ManualScore.objects.create(
                experiment=e,
                score_code=ManualScoreCodeTestCase.manual_score_codes.get(description="unscored"),
                scorer=User.objects.get(username="Test")
            )

        # Score all 8 A05
        for e in ExperimentTestCase.experiments.filter(well="A05")[:6]:
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

        """
        May have to add ExperimentGroup_id to experiment Table
        to group replicates together to speed up query.
        The replicates are identified by the exact well, wormstrain, and
        library stock while the plate id inrciments until there are 8 replicates

        Otherwise, it would have to search for adjacent plate numbers
        with the same well and make sure that they have the same:
            worm strain
            library stock
            well
            date
            temperature
            screen stage

        Unless there is some offset that I could use to partition the different
        screen stages. I think this will be the fastest way, I could make a lookup
        table which would speed things up exponentially.
        """

        score_ids = (ManualScoreTestCase.manual_scores.filter(
            experiment__in=ExperimentTestCase.experiments,
            scorer=UserTestCase.user)
            .values_list('experiment_id', flat=True)
        )

        # Grabbing the fields that won't are universal for the enh sec screen_type
        unscored = (ExperimentTestCase.experiments.exclude(id__in=score_ids)
            .filter(is_junk=False, plate__screen_stage=2)
        )

        # This gets the uniqe entries based on the criteria above
        replicates_plates = (unscored
            .values('well', 'worm_strain_id','library_stock_id','plate__date','plate__temperature')
            .order_by('well', 'worm_strain_id', 'library_stock_id',
            'plate__date', 'plate__temperature').distinct())


        score_ids = []
        for rep in replicates_plates:
            rep_set = unscored.filter(**rep)

            # print "rep_set count",rep_set.count()
            # print "rep_set len",len(rep_set)

            if rep_set.count() > 4:
                score_ids.extend(rep_set
                    .values_list('id', flat=True)[:4])
                # print rep_set.order_by('?')[:4]
            else:
                score_ids.extend(rep_set
                    .values_list('id', flat=True))

        # print ExperimentTestCase.experiments.filter(id__in=score_ids)
            # print "criteria:",rep
            # print "replicates:",
            # print unscored.filter(**rep)
            # print '***********'

    def test_manual_score_chart_view(self):
        '''
        This is the query that will render the necessary data to view
        completeness of genes scored.

        select distinct ExperimentPlate.id,
        	Experiment.id,
        	ManualScore.experiment_id, ManualScore.`score_code_id`,
        	WormStrain.id, WormStrain.`genotype`,
        	LibraryStock.id
        	from Experiment
        	join ManualScore on Experiment.id=ManualScore.`experiment_id`
        	join ExperimentPlate on Experiment.`plate_id`=ExperimentPlate.id
        	join WormStrain on WormStrain.`id`=Experiment.`worm_strain_id`
        	join LibraryStock on Experiment.`library_stock_id`=LibraryStock.id
        	where ExperimentPlate.`screen_stage`=2
        	and Experiment.id in (select ManualScore.experiment_id from ManualScore)
        	and WormStrain.`id` != "N2";
        '''

        exp = (ExperimentTestCase.experiments
            .select_related()
            .prefetch_related()
            .filter(
                id__in=ManualScoreTestCase.manual_scores,
                plate__screen_stage=2
            )
            .exclude(worm_strain="N2")
            .values(
                'pk',
                'plate__id',
                'worm_strain',
                'worm_strain__genotype',
                'manualscore',
                'manualscore__score_code_id__description',
                'library_stock'
            )
            .order_by()
            .distinct()
        )

        print exp

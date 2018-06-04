import unittest
import doctest
import structurebot.assets
from structurebot.assets import Fitting, Asset, Type
from structurebot.config import CONFIG


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(structurebot.assets))
    return tests


class TestAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        name = CONFIG['CORPORATION_NAME']
        cls.assets = list(Asset.from_name(name))
        cls.fittings = []
        test_mod = Type.from_name('Standup Target Painter I')
        for n in range(1, 3):
            fitting = Fitting(MedSlot=[test_mod for x in range(0, n)])
            cls.fittings.append(fitting)
        for n in range(1, 3):
            test_fighter = Type.from_name('Standup Einherji I')
            test_fighter.quantity = n
            fitting = Fitting(MedSlot=[test_mod],
                              FighterBay=[test_fighter])
            cls.fittings.append(fitting)

    def test_group_category(self):
        control_tower = Type.from_name('Amarr Control Tower')
        self.assertEqual(control_tower.group.name, 'Control Tower')
        self.assertEqual(control_tower.group.category.name, 'Starbase')

    def test_assets(self):
        self.assertGreater(len(self.assets), 1)

    def test_multi_page_assets(self):
        self.assertGreater(len(self.assets), 1000)

    def test_fitting_equality(self):
        self.assertEquals(self.fittings[0], self.fittings[0])

    def test_fitting_less(self):
        self.assertLess(self.fittings[0], self.fittings[1])

    def test_fitting_greater(self):
        self.assertGreater(self.fittings[1], self.fittings[0])

    def test_fitting_less_quantity(self):
        self.assertLess(self.fittings[2], self.fittings[3])

    def test_fitting_greater_quantity(self):
        self.assertGreater(self.fittings[3], self.fittings[2])

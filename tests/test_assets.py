import unittest
from random import sample
from copy import deepcopy
from structurebot.assets import CorpAssets
from structurebot.citadels import Structure
from structurebot.config import CONFIG
from structurebot.util import name_to_id


class TestAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corp_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
        cls.assets = CorpAssets(corp_id)
        structures = list(Structure.from_corporation(CONFIG['CORPORATION_NAME']))
        cls.fittings = sample(structures, 1)
        test_mod = {'type_id': 35947,
                    'typeName': 'Standup Target Painter I',
                    'quantity': 1}
        for n in range(1, 3):
            copied = deepcopy(cls.fittings[0])
            copied.fitting.MedSlot.extend([test_mod]*n)
            cls.fittings.append(copied)

    def test_assets(self):
        self.assertGreater(len(self.assets.assets), 1)

    def test_multi_page_assets(self):
        self.assertGreater(len(self.assets.assets), 1000)

    def test_categories(self):
        self.assertGreater(len(self.assets.categories), 1)

    def test_types(self):
        self.assertGreater(len(self.assets.types), 1)

    def test_stations(self):
        self.assertGreater(len(self.assets.stations), 1)

    def test_structures(self):
        self.assertGreater(len(self.assets.structures), 1)

    def test_fitting_equality(self):
        self.assertEquals(self.fittings[0].fitting, self.fittings[0].fitting)

    def test_fitting_less(self):
        self.assertLess(self.fittings[0].fitting, self.fittings[1].fitting)

    def test_fitting_greater(self):
        self.assertGreater(self.fittings[2].fitting, self.fittings[1].fitting)

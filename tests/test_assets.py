import unittest
from structurebot import assets
from structurebot.config import CONFIG
from structurebot.util import name_to_id


class TestAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corp_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
        cls.assets = assets.CorpAssets(corp_id)

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

    def test_fitting(self):
        structures = self.assets.structures.keys()
        structure_assets = self.assets.structures[structures[0]]
        fitting = assets.Fitting.from_assets(structure_assets['children'])
        self.assertIsInstance(str(fitting), basestring)
        self.assertIsInstance(fitting, assets.Fitting)

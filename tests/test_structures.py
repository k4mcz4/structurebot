import unittest
import doctest
from structurebot import citadels
from structurebot import assets
from structurebot.config import CONFIG
from structurebot.util import name_to_id


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(citadels))
    return tests

class TestStructures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.structures = list(citadels.Structure.from_corporation(CONFIG['CORPORATION_NAME']))

    def test_structures(self):
        self.assertGreater(len(self.structures), 1)
        for structure in self.structures:
            self.assertIsInstance(structure, citadels.Structure)
            self.assertIsInstance(structure.fitting, assets.Fitting)
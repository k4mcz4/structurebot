import unittest
import doctest
from structurebot import citadels
from structurebot import assets
from structurebot.config import CONFIG
from structurebot.util import name_to_id


class TestStructures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corp = CONFIG['CORPORATION_NAME']
        cls.structures = citadels.Structure.from_corporation(corp)

    def test_structures(self):
        self.assertGreater(len(self.structures), 0)
        for structure in self.structures:
            self.assertIsInstance(structure, citadels.Structure)
            self.assertIsInstance(structure.fitting, assets.Fitting)


class TestStructureDogma(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raitaru_type = assets.Type.from_name('Raitaru')
        manufacturing_type = assets.Type.from_name('Standup Manufacturing Plant I')
        research_type = assets.Type.from_name('Standup Research Lab I')
        raitaru_fitting = assets.Fitting(ServiceSlot=[manufacturing_type,
                                                      research_type])
        cls.raitaru = citadels.Structure(1, raitaru_type.type_id,
                                         raitaru_type.name,
                                         fitting=raitaru_fitting)

    def test_fuel(self):
        self.assertEqual(self.raitaru.fuel_rate, 18)
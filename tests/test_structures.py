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
        quantum_core = assets.Type.from_name('Raitaru Upwell Quantum Core')
        raitaru_fitting = assets.Fitting(ServiceSlot=[manufacturing_type,
                                                      research_type],
                                         QuantumCoreRoom=[quantum_core])
        cls.raitaru = citadels.Structure(1, type_id=raitaru_type.type_id,
                                         type_name=raitaru_type.name,
                                         fitting=raitaru_fitting)
        cls.unfit_raitaru = citadels.Structure(2, type_id=raitaru_type.type_id,
                                               type_name=raitaru_type.name)

    def test_fitting(self):
        self.assertTrue(self.raitaru.fitting)
        self.assertFalse(self.unfit_raitaru.fitting)

    def test_fuel(self):
        self.assertEqual(self.raitaru.fuel_rate, 18)
        # Do twice to test caching
        self.assertEqual(self.raitaru.fuel_rate, 18)
        # Test unfit structure
        self.assertEqual(self.unfit_raitaru.fuel_rate, 0)


    def test_core(self):
        self.assertTrue(self.raitaru.has_core)
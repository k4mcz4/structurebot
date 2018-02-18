import unittest
import doctest
from structurebot import pos
from structurebot.config import CONFIG
from structurebot.util import name_to_id, esi, esi_client


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(pos))
    return tests


class TestPOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        CONFIG['CORP_ID'] = cls.corp_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
        corporation_id_request = esi.op['get_corporations_corporation_id'](corporation_id=cls.corp_id)
        corporation_id = esi_client.request(corporation_id_request).data
        cls.alliance_id = corporation_id.get('alliance_id', None)

    def test_sov(self):
        sov_ids = pos.sov_systems(self.alliance_id)
        for system in sov_ids:
            self.assertIsInstance(system, int)

    def test_check_pos(self):
        [self.assertIsInstance(s, str) for s in pos.check_pos()]
from __future__ import absolute_import
import doctest
from structurebot import util


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(util))
    return tests

#!/usr/bin/env python

from assets import CorpAssets
from citadels import Structure
from config import CONFIG
from util import access_token, name_to_id


if __name__ == '__main__':
    corp_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    assets = CorpAssets(corp_id)
    structures = Structure.from_corporation(CONFIG['CORPORATION_NAME'], access_token, assets.assets)
    total_fuel = 0
    for structure in sorted(structures, key=lambda x: x.name):
        if 'Rented by' in structure.name:
            continue
        print structure
        print 'Fuel/Cycle: {}'.format(structure.fuel_rate)
        print structure.fitting
        print '-----'
        total_fuel += structure.fuel_rate

    print 'Total fuel/cycle: {}'.format(total_fuel)

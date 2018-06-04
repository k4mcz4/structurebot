#!/usr/bin/env python

import logging

from structurebot.citadels import Structure
from structurebot.config import CONFIG


if __name__ == '__main__':
    level = logging.WARNING
    if CONFIG['DEBUG']:
        level = logging.INFO
    logging.basicConfig(level=level)
    structures = Structure.from_corporation(CONFIG['CORPORATION_NAME'])
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

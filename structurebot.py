#!/usr/bin/env python

import logging
import argparse

from structurebot.config import CONFIG
from structurebot.util import notify_slack, name_to_id
from structurebot.citadels import Structure
from structurebot.assets import Asset
from structurebot.pos import check_pos


level = logging.WARNING
if CONFIG['DEBUG']:
    level = logging.INFO
logging.basicConfig(level=level)

parser = argparse.ArgumentParser()
parser.add_argument('--suppress-upcoming-detonations', dest='upcoming_detonations', action='store_false')
parser.add_argument('--suppress-unscheduled-detonations', dest='unscheduled_detonations', action='store_false')
parser.add_argument('--suppress-ansiblex-ozone', dest='ansiblex_ozone', action='store_false')
parser.add_argument('--suppress-fuel-warning', dest='fuel_warning', action='store_false')
parser.add_argument('--suppress-service-state', dest='service_state', action='store_false')
parser.add_argument('--suppress-structure-state', dest='structure_state', action='store_false')

args = parser.parse_args()

messages = []
try:
    corp_name = CONFIG['CORPORATION_NAME']
    CONFIG['CORP_ID'] = name_to_id(corp_name, 'corporation')
    assets = Asset.from_name(corp_name)
    structures = Structure.from_corporation(corp_name, assets)
    messages = []
    for structure in structures:
        message = []
        if not structure.accessible:
            msg = 'Found an inaccesible citadel ({}) in {}'.format(structure.structure_id, structure.system_id)
            messages.append(msg)
            continue
        if args.unscheduled_detonations and structure.needs_detonation:
            message.append('Needs to have an extraction scheduled')
        if args.upcoming_detonations and structure.detonates_soon:
            message.append('Ready to detonate {}'.format(structure.detonation))
        if args.ansiblex_ozone and structure.needs_ozone:
            message.append('Low on Liquid Ozone: {}'.format(structure.jump_fuel))
        if args.fuel_warning and structure.needs_fuel:
            message.append('Runs out of fuel on {}'.format(structure.fuel_expires))
            if args.service_state:
                if structure.online_services:
                    message.append('Online Services: {}'.format(', '.join(structure.online_services)))
                if structure.offline_services:
                    message.append('Offline Services: {}'.format(', '.join(structure.offline_services)))
        if args.service_state and structure.offline_services:
            message.append('Offline services: {}'.format(', '.join(structure.offline_services)))
        if args.structure_state and (structure.vulnerable or structure.reinforced):
            state = structure.state.replace('_', ' ').title()
            message.append('{} until {}'.format(state, structure.state_timer_end))
        if message:
            messages.append(u'\n'.join([u'{}'.format(structure.name)] + message))
	messages += check_pos(corp_name, assets)
except Exception, e:
    if CONFIG['DEBUG']:
        raise
    else:
        messages = [str(e)]
if messages:
	messages.insert(0, ' Upcoming {} Structure Maintenence Tasks'.format(corp_name))
	notify_slack(sorted(messages))



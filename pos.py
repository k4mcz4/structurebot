
from config import *
from util import xml_api, access_token, esi_api
from util import pprinter, annotate_element, name_to_id
from pos_resources import pos_fuel, moon_goo, pos_mods, fuel_types
import sys
import math
from decimal import Decimal


def nearest(source, destinations):
    (sx, sy, sz) = [Decimal(n) for n in source]
    nearest = sys.maxint
    nearest_idx = None
    for (idx, destination) in destinations.iteritems():
        (dx, dy, dz) = [Decimal(n) for n in destination]
        distance = math.sqrt(math.pow(sx-dx, 2) +
                             math.pow(sy-dy, 2) +
                             math.pow(sz-dz, 2))
        if distance < nearest:
            nearest = distance
            nearest_idx = idx
    return nearest_idx


def pos_assets():
    corp_id = name_to_id(CORPORATION_NAME, 'corporation')
    asset_xml = xml_api('/corp/AssetList.xml.aspx',
                        params={'corporationID': corp_id},
                        xpath='.//rowset[@name="assets"]/row[@singleton="1"]')
    pos = {}
    mods = {}
    for row in asset_xml:
        typeID = int(row.get('typeID'))
        # Filter out things that aren't POS mods
        if typeID not in pos_mods:
            continue
        # Decorate POS mods with SDE data
        annotate_element(row, pos_mods[typeID])
        itemID = int(row.get('itemID'))
        if row.get('groupName') == 'Control Tower':
            pos_stuff = pos
        else:
            pos_stuff = mods
        pos_stuff[itemID] = row.attrib
        for contents in row.findall('.//rowset[@name="contents"]/row'):
            typeID = int(contents.get('typeID'))
            # Decorate POS mod contents with SDE data
            if typeID in moon_goo:
                annotate_element(contents, moon_goo[typeID])
            elif typeID in fuel_types:
                annotate_element(contents, fuel_types[typeID])
            else:
                continue
            parents_contents = pos_stuff[itemID].setdefault('contents', [])
            parents_contents.append(contents.attrib)
    locations = item_locations(pos.keys() + mods.keys())
    for itemID, location in locations.iteritems():
        try:
            pos[itemID].update(location)
        except KeyError:
            mods[itemID].update(location)
    pos_locations = {i: (pos[i]['x'], pos[i]['y'], pos[i]['z']) for i in pos}
    for i, d in mods.iteritems():
        try:
            location = (d['x'], d['y'], d['z'])
        except KeyError:
            print '{} ({}) has no coordinates'.format(d['typeName'], i)
            continue
        nearest_pos = nearest(location, pos_locations)
        parent_pos_mods = pos[nearest_pos].setdefault('mods', [])
        if d['groupName'] == 'Silo':
            if pos[nearest_pos]['raceName'] == 'Amarr':
                d['capacity'] = Decimal(d['capacity'])*Decimal(1.5)
            if pos[nearest_pos]['raceName'] == 'Gallente':
                d['capacity'] = Decimal(d['capacity'])*Decimal(2)
        parent_pos_mods.append(d)
    return pos


def item_locations(ids):
    corp_id = name_to_id(CORPORATION_NAME, 'corporation')
    location_dict = {}
    chunks = 1000
    for items in [ids[i:i+chunks] for i in range(0, len(ids), chunks)]:
        locations = esi_api('Assets.post_corporations_corporation_id_assets_locations', token=access_token, item_ids=items, corporation_id=corp_id)
        for location in locations:
            i = int(location.get('item_id'))
            location_dict[i] = location
    return location_dict


def sov_systems(sov_holder_id):
    sov_systems = []
    if sov_holder_id:
        map_sov = esi_api('Sovereignty.get_sovereignty_map')
        for system in map_sov:
            try:
                if system['alliance_id'] == sov_holder_id:
                    sov_systems.append(system['system_id'])
            except KeyError:
                continue
    return sov_systems


def check_pos():
    corp_id = name_to_id(CORPORATION_NAME, 'corporation')
    pos_list = esi_api('Corporation.get_corporations_corporation_id_starbases', token=access_token, corporation_id=corp_id)
    poses = pos_assets()
    messages = []
    alliance_id = esi_api('Corporation.get_corporations_corporation_id', corporation_id=corp_id).get('alliance_id', None)
    sovs = sov_systems(alliance_id)
    for pos in pos_list:
        pos_id = int(pos.get('starbase_id'))
        type_id = int(pos.get('type_id'))
        system_id = int(pos.get('system_id'))
        state = pos.get('state')
        if not state:
            print 'POS {} is unanchored, skipping'.format(pos_id)
            continue
        location_name = esi_api('Universe.get_universe_systems_system_id',
                                system_id=system_id).get('name')
        moon_id = int(pos.get('moon_id'))
        moon_name = esi_api('Universe.get_universe_moons_moon_id',
                            moon_id=moon_id).get('name')
        sov = system_id in sovs
        poses[pos_id]['location_name'] = location_name
        poses[pos_id]['moon_name'] = moon_name
        poses[pos_id]['moon_id'] = moon_id
        has_stront = False
        has_fuel = False
        has_defensive_mods = False
        # TODO: handle purposefully offlined POS by checking for fuel
        for fuel in poses[pos_id].get('contents', []):
            fuel_type_id = int(fuel.get('typeID'))
            quantity = int(fuel.get('quantity'))
            multiplier = .75 if sov else 1.0
            rate = pos_fuel[type_id][fuel_type_id] * multiplier
            fuel['hourly_rate'] = rate
            if fuel_type_id == 16275:
                has_stront = True
                if state == 'offline':
                    continue
                reinforce_hours = int(quantity / rate)
                message = '{} has {} hours of stront'.format(moon_name,
                                                             reinforce_hours)
                if reinforce_hours < STRONT_HOURS:
                    messages.append(message)
            else:
                has_fuel = True
                if state == 'offline':
                    continue
                how_soon = int(quantity / (rate*24))
                days = 'day' if how_soon == 1 else 'days'
                message = '{} has {} {} of fuel'.format(moon_name,
                                                        how_soon,
                                                        days)
                if how_soon < TOO_SOON:
                    messages.append(message)
        for mod in poses[pos_id].get('mods', []):
            # Note this is currently only useful for
            # silos that are being filled (e.g. mining),
            # not emptied (e.g. reaction inputt)
            if mod['typeName'] == 'Silo':
                try:
                    goo = mod['contents'][0]
                except KeyError:
                    goo = None
                if goo:
                    capacity = Decimal(mod['capacity'])
                    name = goo['typeName']
                    volume = Decimal(goo['volume'])
                    quantity = int(goo['quantity'])
                    total_volume = volume*quantity
                    rate = volume*100*24
                    remaining_capacity = capacity - total_volume
                    days_remaining = int(remaining_capacity / rate)
                    days = 'day' if days_remaining == 1 else 'days'
                    message = "{} has {} {} of {} capacity left ({} current units)".format(moon_name, days_remaining, days, name, quantity)
                    if days_remaining < TOO_SOON:
                        messages.append(message)
            if mod['groupName'] == 'Shield Hardening Array':
                has_defensive_mods = True
        if state != 'online':
            if has_fuel and state == 'offline' and not has_defensive_mods:
                continue
            statetime = pos.get('stateTimestamp')
            message = '{} is {}'.format(moon_name, state)
            if statetime:
                state_predicates = {
                    'reinforced': 'until'
                }
                message += ' {} {}'.format(state_predicates.get(state, 'since'), statetime)
            messages.append(message)
    return messages

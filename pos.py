
from config import *
from util import xml_api, esi_api
from util import pprinter, annotate_element
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


def pos_assets(corp_id=CORPORATION_ID):
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
        location = (d['x'], d['y'], d['z'])
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
    location_dict = {}
    chunks = 100
    for items in [ids[i:i+chunks] for i in range(0, len(ids), chunks)]:
        locations_xml = xml_api('/corp/Locations.xml.aspx',
                                params={'ids': ','.join(str(id)
                                                        for id in items)},
                                xpath='.//rowset[@name="locations"]/row')
        for location in locations_xml:
            i = int(location.get('itemID'))
            location_dict[i] = {k: location.attrib[k]
                                for k in ['itemName', 'x', 'y', 'z']}
    return location_dict


def sov_systems(sov_holder):
    sov_holder_id = esi_api('Search.get_search',
                            categories=['alliance'],
                            search=sov_holder,
                            strict=True).get('alliance')[0]
    map_sov = esi_api('Sovereignty.get_sovereignty_map')
    sov_systems = []
    for system in map_sov:
        try:
            if system['alliance_id'] == sov_holder_id:
                sov_systems.append(system['system_id'])
        except KeyError:
            continue
    return sov_systems


def check_pos():
    pos_list_xml = xml_api('/corp/StarbaseList.xml.aspx')
    poses = pos_assets()
    messages = []
    sovs = sov_systems(SOV_HOLDER)
    for pos in pos_list_xml.findall('.//rowset[@name="starbases"]/row'):
        pos_id = int(pos.get('itemID'))
        type_id = int(pos.get('typeID'))
        location_id = int(pos.get('locationID'))
        states = ('Unanchored', 'Offline', 'Onlining', 'Reinforced', 'Online')
        state = states[int(pos.get('state'))]
        location_name = esi_api('Universe.get_universe_systems_system_id',
                                system_id=location_id).get('name')
        moon_id = int(pos.get('moonID'))
        moon_name = esi_api('Universe.get_universe_moons_moon_id',
                            moon_id=moon_id).get('name')
        sov = location_id in sovs
        poses[pos_id]['locationName'] = location_name
        poses[pos_id]['moonName'] = moon_name
        poses[pos_id]['moonID'] = moon_id
        for fuel in poses[pos_id]['contents']:
            fuel_type_id = int(fuel.get('typeID'))
            quantity = int(fuel.get('quantity'))
            multiplier = .75 if sov else 1.0
            rate = pos_fuel[type_id][fuel_type_id] * multiplier
            fuel['hourly_rate'] = rate
            if fuel_type_id == 16275:
                reinforce_hours = int(quantity / rate)
                message = '{} has {} hours of stront'.format(moon_name,
                                                             reinforce_hours)
                if reinforce_hours < STRONT_HOURS:
                    messages.append(message)
            else:
                how_soon = int(quantity / (rate*24))
                days = 'day' if how_soon == 1 else 'days'
                message = '{} has {} {} of fuel'.format(moon_name,
                                                        how_soon,
                                                        days)
                if how_soon < TOO_SOON:
                    messages.append(message)
        for mod in poses[pos_id]['mods']:
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
        if state != 'Online':
            statetime = pos.get('stateTimestamp')
            message = '{} is {}'.format(moon_name, state)
            if statetime:
                message += ' until {}'.format(statetime)
            messages.append(message)
    return messages

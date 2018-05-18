
from config import CONFIG
from util import esi, esi_client, annotate_element, name_to_id
from assets import CorpAssets, is_system_id
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


def pos_assets(corporation_id, assets={}):
    '''Takes a corp id and optional dict of assets and gathers location data
       for POS mods
    
    Args:
        corporation_id (int): corp id
        assets (dict): dict of assets
    
    Returns:
        dict: dict of pos structure assets with location data

    >>> CONFIG['CORP_ID'] = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    >>> type(pos_assets(CONFIG['CORP_ID']))
    <type 'dict'>
    '''
    if not assets:
        assets = CorpAssets(corporation_id).assets
    pos = {}
    mods = {}
    for item_id, asset in assets.iteritems():
        if not is_system_id(asset.get('location_id')):
            continue
        # Filter out things that aren't POS mods
        type_id = int(asset.get('type_id'))
        if type_id not in pos_mods:
            continue
        # Decorate POS mods with SDE data
        annotate_element(asset, pos_mods[type_id])
        if asset.get('groupName') == 'Control Tower':
            pos_stuff = pos
        else:
            pos_stuff = mods
        pos_stuff[item_id] = asset
    locations = item_locations(pos.keys() + mods.keys())
    for itemID, location in locations.iteritems():
        try:
            pos[itemID].update(location)
        except KeyError:
            mods[itemID].update(location)
    pos_locations = {i: (pos[i]['position']['x'], pos[i]['position']['y'],
                         pos[i]['position']['z']) for i in pos}
    for i, d in mods.iteritems():
        try:
            location = (d['position']['x'], d['position']['y'],
                        d['position']['z'])
        except KeyError:
            print '{} ({}) has no coordinates'.format(d['typeName'], i)
            continue
        nearest_pos = nearest(location, pos_locations)
        parent_pos_mods = pos[nearest_pos].setdefault('mods', [])
        parent_pos_mods.append(d)
    return pos


def item_locations(ids):
    """Returns dict of location coordinates for a list of item ids
    
    Args:
        ids (list): list of item ids
    
    Returns:
        dict: dict of location coordinates keyed by item id
    """
    location_dict = {}
    chunks = 1000
    for items in [ids[i:i+chunks] for i in range(0, len(ids), chunks)]:
        locations_request = esi.op['post_corporations_corporation_id_assets_locations'](item_ids=items, corporation_id=CONFIG['CORP_ID'])
        locations = esi_client.request(locations_request).data
        for location in locations:
            i = int(location.get('item_id'))
            location_dict[i] = location
    return location_dict


def sov_systems(sov_holder_id):
    """Returns a list of system IDs held by sov holder
    
    Args:
        sov_holder_id (int): Alliance ID
    
    Returns:
        list: List of system ID (int) held by sov holder
    """
    sov_systems = []
    if sov_holder_id:
        map_sov_request = esi.op['get_sovereignty_map']()
        map_sov = esi_client.request(map_sov_request).data
        for system in map_sov:
            try:
                if system['alliance_id'] == sov_holder_id:
                    sov_systems.append(system['system_id'])
            except KeyError:
                continue
    return sov_systems


def check_pos():
    """
    Check POS for fuel and status
    
    Returns:
        list: list of alert strings

    """
    corp_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    pos_list_request = esi.op['get_corporations_corporation_id_starbases'](corporation_id=corp_id)
    pos_list = esi_client.request(pos_list_request).data
    poses = pos_assets(corp_id)
    messages = []
    alliance_id_request = esi.op['get_corporations_corporation_id'](corporation_id=corp_id)
    alliance_id = esi_client.request(alliance_id_request).data.get('alliance_id', None)
    sovs = sov_systems(alliance_id)
    for pos in pos_list:
        pos_id = int(pos.get('starbase_id'))
        type_id = int(pos.get('type_id'))
        system_id = int(pos.get('system_id'))
        state = pos.get('state')
        if not state:
            print 'POS {} is unanchored, skipping'.format(pos_id)
            continue
        location_name_request = esi.op['get_universe_systems_system_id'](system_id=system_id)
        location_name = esi_client.request(location_name_request).data.get('name')
        moon_id = int(pos.get('moon_id'))
        moon_name_request = esi.op['get_universe_moons_moon_id'](moon_id=moon_id)
        moon_name = esi_client.request(moon_name_request).data.get('name')
        sov = system_id in sovs
        poses[pos_id]['location_name'] = location_name
        poses[pos_id]['moon_name'] = moon_name
        poses[pos_id]['moon_id'] = moon_id
        has_stront = False
        has_fuel = False
        has_defensive_mods = False
        fuel_request = esi.op['get_corporations_corporation_id_starbases_starbase_id'](corporation_id=corp_id, starbase_id=pos_id,
                                                                                           system_id=system_id)
        fuel = esi_client.request(fuel_request).data.get('fuels')
        for fuel in fuel:
            fuel_type_id = int(fuel.get('type_id'))
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
                if reinforce_hours < CONFIG['STRONT_HOURS']:
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
                if how_soon < CONFIG['TOO_SOON']:
                    messages.append(message)
        for mod in poses[pos_id].get('mods', []):
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

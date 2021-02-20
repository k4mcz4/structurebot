
from __future__ import absolute_import
from .config import CONFIG
from .util import esi, esi_client, name_to_id, HTTPError
from .assets import Asset, Type, is_system_id
from .pos_resources import pos_fuel
import sys
import math
import datetime
from decimal import Decimal
import six
from six.moves import range


def nearest(source, destinations):
    (sx, sy, sz) = (source['x'], source['y'], source['z'])
    nearest = sys.maxsize
    nearest_idx = None
    for (idx, destination) in six.iteritems(destinations):
        (dx, dy, dz) = (destination['x'], destination['y'], destination['z'])
        distance = math.sqrt(math.pow(sx-dx, 2) +
                             math.pow(sy-dy, 2) +
                             math.pow(sz-dz, 2))
        if distance < nearest:
            nearest = distance
            nearest_idx = idx
    return nearest_idx


class Pos(Asset):
    """docstring for Pos"""
    def __init__(self, system_id, moon_id, state, unanchor_at,
                 reinforced_until, onlined_since, fuel_bay_view, fuel_bay_take,
                 anchor, unanchor, online, offline, allow_corporation_members,
                 allow_alliance_members, use_alliance_standings,
                 attack_if_other_security_status_dropping, attack_if_at_war,
                 fuels=[], mods=[], attack_security_status_threshold=None, 
                 attack_standing_threshold=None, *args, **kwargs):
        super(Pos, self).__init__(*args, **kwargs)
        self.system_id = system_id
        self.moon_id = moon_id
        self.state = state
        self.unanchor_at = unanchor_at
        self.reinforced_until = reinforced_until
        self.onlined_since = onlined_since
        self.fuel_bay_view = fuel_bay_view
        self.fuel_bay_take = fuel_bay_take
        self.anchor = anchor
        self.unanchor = unanchor
        self.online = online
        self.offline = offline
        self.allow_corporation_members = allow_corporation_members
        self.allow_alliance_members = allow_alliance_members
        self.use_alliance_standings = use_alliance_standings
        self.attack_standing_threshold = attack_standing_threshold
        self.attack_security_status_threshold = attack_security_status_threshold
        self.attack_if_other_security_status_dropping = attack_if_other_security_status_dropping
        self.attack_if_at_war = attack_if_at_war
        self.fuels = [Asset.from_id(t.type_id, quantity=t.quantity)
                      for t in fuels]
        self.mods = mods

    @classmethod
    def from_id(cls, corp_id, starbase_id, type_id, system_id, moon_id, state,
                unanchor_at=None, reinforced_until=None, onlined_since=None, mods=[], **kwargs):
        pos_data = {
            'item_id': starbase_id,
            'type_id': type_id,
            'location_id': system_id,
            'moon_id': moon_id,
            'state': state,
            'unanchor_at': unanchor_at,
            'reinforced_until': reinforced_until,
            'onlined_since': onlined_since,
            'mods': mods
        }
        op = 'get_corporations_corporation_id_starbases_starbase_id'
        pos_request = esi.op[op](corporation_id=corp_id,
                                 starbase_id=starbase_id, system_id=system_id)
        pos_response = esi_client.request(pos_request)
        if pos_response.status == 200:
            pos = pos_response.data
            pos_data.update(pos)
            pos_data.update(kwargs)
            return cls(system_id=system_id, **pos_data)

    @classmethod
    def from_name(self):
        raise NotImplemented

    @staticmethod
    def from_corp_name(corp_name, corp_assets=None):
        pos_mod_dict = {}
        pos_list = []
        corp_assets = corp_assets or Asset.from_entity_name(corp_name)
        assets = [a for a in corp_assets if Pos.is_pos_mod(a)]
        pos_mods = [m for m in assets if m.group.name != 'Control Tower']
        mod_locations = item_locations([m.item_id for m in pos_mods])
        pos_assets = {p.item_id: p for p in assets if p.group.name == 'Control Tower'}
        pos_locations = item_locations([p.item_id for p in pos_assets.values()])
        for mod in pos_mods:
            mod.xyz = mod_locations[mod.item_id]
            mods = pos_mod_dict.setdefault(nearest(mod.xyz, pos_locations), [])
            mods.append(mod)
        corp_id = name_to_id(corp_name, 'corporation')
        poses_request = esi.op['get_corporations_corporation_id_starbases'](corporation_id=corp_id)
        poses_response = esi_client.request(poses_request)
        if not poses_response.status == 200:
            raise HTTPError(poses_response.data['error'])
        poses = {s.starbase_id: s for s in poses_response.data}
        for pos_id, pos in six.iteritems(poses):
            pos.update(pos_assets[pos.starbase_id].__dict__)
            pos['xyz'] = pos_locations[pos.starbase_id]
            pos_object = Pos.from_id(corp_id=corp_id, mods=pos_mod_dict.get(pos_id, []), **pos)
            pos_list.append(pos_object)
        return pos_list

    @staticmethod
    def is_pos_mod(asset):
        if not is_system_id(asset.location_id):
            return False
        # Filter out things that aren't POS mods
        if asset.group.category.name != 'Starbase':
            return False
        return True

    @property
    def system_name(self):
        try:
            return self._system_name
        except AttributeError:
            self._system_name = None
            location_name_request = esi.op['get_universe_systems_system_id'](system_id=self.system_id)
            location_name_response = esi_client.request(location_name_request)
            if location_name_response.status == 200:
                self._system_name = location_name_response.data.get('name')
            return self._system_name
    
    @property
    def moon_name(self):
        try:
            return self._moon_name
        except AttributeError:
            moon_name_request = esi.op['get_universe_moons_moon_id'](moon_id=self.moon_id)
            moon_name_response = esi_client.request(moon_name_request)
            if moon_name_response.status == 200:
                self._moon_name = moon_name_response.data.get('name')
            return self._moon_name
        

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
        op = 'post_corporations_corporation_id_assets_locations'
        locations_request = esi.op[op](item_ids=items,
                                       corporation_id=CONFIG['CORP_ID'])
        locations = esi_client.request(locations_request).data
        for location in locations:
            i = int(location.get('item_id'))
            location_dict[i] = location.position
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
                if system.get('alliance_id', 0) == sov_holder_id:
                    sov_systems.append(system['system_id'])
            except KeyError:
                continue
    return sov_systems


def check_pos(corp_name, corp_assets=None):
    """
    Check POS for fuel and status
    
    Returns:
        list: list of alert strings

    """
    messages = []
    corp_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    pos_list = Pos.from_corp_name(corp_name, corp_assets)
    if not pos_list:
        return messages
    alliance_id_request = esi.op['get_corporations_corporation_id'](corporation_id=corp_id)
    alliance_id = esi_client.request(alliance_id_request).data.get('alliance_id', None)
    sovs = sov_systems(alliance_id)
    for pos in pos_list:
        # TODO: All this could be done in the Pos object for easier testing
        # But POS are going away ;)
        sov = pos.system_id in sovs
        has_stront = False
        has_fuel = False
        has_defensive_mods = False
        for fuel in pos.fuels:
            multiplier = .75 if sov else 1.0
            rate = pos_fuel[pos.type_id][fuel.type_id] * multiplier
            if fuel.type_id == 16275:
                has_stront = True
                if pos.state == 'offline':
                    continue
                reinforce_hours = int(fuel.quantity / rate)
                if reinforce_hours < CONFIG['STRONT_HOURS']:
                    message = '{} has {} hours of stront'.format(pos.moon_name, reinforce_hours)
                    messages.append(message)
            else:
                has_fuel = True
                if pos.state == 'offline':
                    continue
                how_soon = datetime.timedelta(fuel.quantity / (rate*24))
                if how_soon < CONFIG['TOO_SOON']:
                    days = 'day' if how_soon == 1 else 'days'
                    message = '{} has {} {} of fuel'.format(pos.moon_name, how_soon, days)
                    messages.append(message)
        for mod in pos.mods:
            if mod.group.name == 'Shield Hardening Array':
                has_defensive_mods = True
        if pos.state != 'online':
            if has_fuel and pos.state == 'offline' and not has_defensive_mods:
                continue
            message = '{} is {}'.format(pos.moon_name, pos.state)
            if pos.reinforced_until:
                state_predicates = {
                    'reinforced': 'until'
                }
                message += ' {} {}'.format(state_predicates.get(pos.state, 'since'), pos.reinforced_until)
            messages.append(message)
    return messages

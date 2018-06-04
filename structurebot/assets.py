import sqlite3
import json
from collections import Counter

from config import CONFIG
from util import esi, esi_client, name_to_id, names_to_ids, HTTPError


def is_system_id(location_id):
    if location_id >= 30000000 and location_id <= 32000000:
        return True
    else:
        return False

def is_station_id(location_id):
    if location_id >= 60000000 and location_id <= 64000000:
        return True
    else:
        return False

class Category(object):
    """docstring for Category"""
    def __init__(self, category_id, name, published, groups):
        super(Category, self).__init__()
        self.category_id = category_id
        self.name = name
        self.published = published
        self.category_id = category_id
        self.groups = groups

    @classmethod
    def from_id(cls, id):
        if not isinstance(id, int):
            raise ValueError('Type ID must be an integer')
        op = 'get_universe_categories_category_id'
        type_request = esi.op[op](category_id=id)
        type_response = esi_client.request(type_request)
        if type_response.status == 200:
            return cls(**type_response.data)
        else:
            raise HTTPError(type_response.data['error'])

    @classmethod
    def from_ids(cls, ids):
        types = []
        for id in ids:
            types.append(cls.from_id(id))
        return types


class Group(object):
    """docstring for Group"""
    def __init__(self, group_id, name, published, category_id, types,
                 category=None):
        super(Group, self).__init__()
        self.group_id = group_id
        self.name = name
        self.published = published
        self.category_id = category_id
        self.types = types
        self.category = category or Category.from_id(category_id)

    @classmethod
    def from_id(cls, id):
        if not isinstance(id, int):
            raise ValueError('Type ID must be an integer')
        type_request = esi.op['get_universe_groups_group_id'](group_id=id)
        type_response = esi_client.request(type_request)
        if type_response.status == 200:
            return cls(**type_response.data)
        else:
            raise HTTPError(type_response.data['error'])

    @classmethod
    def from_ids(cls, ids):
        types = []
        for id in ids:
            types.append(cls.from_id(id))
        return types


class BaseType(object):
    """Base EVE SDE Type"""
    def __init__(self, type_id, name, description, published, group_id,
                 group=None, market_group_id=None, radius=None, volume=None,
                 packaged_volume=None, icon_id=None, capacity=None,
                 portion_size=None, mass=None, graphic_id=None,
                 dogma_attributes=[], dogma_effects=[]):
        super(BaseType, self).__init__()
        self.type_id = type_id
        self.name = name
        self.description = description
        self.published = published
        self.group_id = group_id
        self.group = group or Group.from_id(group_id)
        self.market_group_id = market_group_id
        self.radius = radius
        self.volume = volume
        self.packaged_volume = packaged_volume
        self.icon_id = icon_id
        self.capacity = capacity
        self.portion_size = portion_size
        self.mass = mass
        self.graphic_id = graphic_id
        self.dogma_attributes = dogma_attributes
        self.dogma_effects = dogma_effects

    def __str__(self):
        return '{} - ({})'.format(self.name, self.type_id)


class Type(BaseType):
    """EVE SDE Type with bulk constructors"""
    def __init__(self, quantity=1, *args, **kwargs):
        super(Type, self).__init__(*args, **kwargs)
        self.quantity = quantity

    @classmethod
    def from_id(cls, id, quantity=1):
        """Return Type from id

        Args:
            id (int): EVE SDE Type id

        Returns:
            Type: Type matching id

        Raises:
            HTTPError: Unexpected ESI error
            ValueError: Not an int
        """
        if not isinstance(id, int):
            raise ValueError('Type ID must be an integer')
        type_request = esi.op['get_universe_types_type_id'](type_id=id)
        type_response = esi_client.request(type_request)
        if type_response.status == 200:
            return cls(quantity=quantity, **type_response.data)
        else:
            raise HTTPError(type_response.data['error'])

    @classmethod
    def from_ids(cls, ids):
        """Returns Types from a list of type IDs

        Args:
            ids (list of ints): list of EVE SDE Type IDs (invalid are ignored)

        Returns:
            list: EVE SDE Types
        """
        types = []
        for id in ids:
            types.append(cls.from_id(id))
        return types

    @classmethod
    def from_name(cls, name):
        """Return a Type from a type name

        Args:
            name (str): Name of an EVE SDE Type

        Returns:
            Type: Type matching name
        """
        id = name_to_id(name, 'inventory_type')
        return cls.from_id(id)

    @classmethod
    def from_names(cls, names):
        """Returns Types from a list of Type names

        Args:
            names (list of str): list of EVE SDE Type names

        Returns:
            TYPE: Description

        >>> [str(i) for i in Type.from_names(['125mm Gatling AutoCannon II'])]
        ['125mm Gatling AutoCannon II - (2873)']
        """
        ids = names_to_ids(names)['inventory_types'].values()
        return cls.from_ids(ids)


class Asset(BaseType):
    """EVE Asset Item"""

    def __init__(self, location_id, location_type, quantity, item_id,
                 is_singleton, location_flag, is_blueprint_copy=None,
                 xyz=None, *args, **kwargs):
        super(Asset, self).__init__(*args, **kwargs)
        self.location_id = location_id
        self.location_type = location_type
        self.quantity = quantity
        self.item_id = item_id
        self.is_singleton = is_singleton
        self.location_flag = location_flag
        self.xyz = xyz

    @classmethod
    def from_id(cls, id, id_type):
        """Returns Assets owned by id of id_type

        Args:
            id (int): Asset owner id
            id_type (TYPE): Type of Asset owner (characters or corporations)

        Returns:
            list: Assets owned by id
        """
        assets = []
        assets_request = None
        params = {'page': 1}
        if id_type == 'characters':
            params['character_id'] = id
            op = 'get_characters_character_id_assets'
        elif id_type == 'corporations':
            params['corporation_id'] = id
            op = 'get_corporations_corporation_id_assets'
        pages_left = params['page']
        while(pages_left):
            assets_request = esi.op[op](**params)
            assets_response = esi_client.request(assets_request,
                                                 raw_body_only=True)
            assets_api = json.loads(assets_response.raw)
            for asset in assets_api:
                asset_type = Type.from_id(asset['type_id'])
                asset.update(asset_type.__dict__)
                assets.append(cls(**asset))
            pages = assets_response.header['X-Pages'][0]
            pages_left = pages - params['page']
            params['page'] += 1
        return assets

    @classmethod
    def from_name(cls, name):
        """Return Assets owned by owner name

        Args:
            name (string): Character or Corporation name

        Returns:
            list: List of Assets
        """
        id_results = names_to_ids([name])
        id = None
        id_type = None
        if 'characters' in id_results:
            id_type = 'characters'
        elif 'corporations' in id_results:
            id_type = 'corporations'
        else:
            return None
        id = id_results[id_type][name]
        return cls.from_id(id, id_type)


def is_system_id(location_id):
    if location_id >= 30000000 and location_id <= 32000000:
        return True
    else:
        return False


class Fitting(object):
    """docstring for Fitting"""

    slots = ['Cargo', 'DroneBay', 'FighterBay', 'FighterTube', 'HiSlot',
             'LoSlot', 'MedSlot', 'RigSlot', 'ServiceSlot', 'SubSystemSlot']

    def __init__(self, Cargo=[], DroneBay=[], FighterBay=[], FighterTube=[],
                 HiSlot=[], LoSlot=[], MedSlot=[], RigSlot=[], ServiceSlot=[],
                 SubSystemSlot=[]):
        super(Fitting, self).__init__()
        self.Cargo = Cargo
        self.DroneBay = DroneBay
        self.FighterBay = FighterBay
        self.FighterTube = FighterTube
        self.HiSlot = HiSlot
        self.LoSlot = LoSlot
        self.MedSlot = MedSlot
        self.RigSlot = RigSlot
        self.ServiceSlot = ServiceSlot
        self.SubSystemSlot = SubSystemSlot

    @classmethod
    def from_assets(cls, assets):
        fittings = {slot: [] for slot in Fitting.slots}
        for asset in assets:
            flag = asset.location_flag
            if not flag:
                continue
            for slot in Fitting.slots:
                if flag.startswith(slot):
                    fittings[slot].append(asset)
                    fit = True
        return cls(**fittings)

    @staticmethod
    def _name_count(asset):
        name = asset.name
        if asset.quantity > 1:
            name += ' ({})'.format(asset.quantity)
        return name

    def __cmp__(self, other):
        if not isinstance(other, Fitting):
            raise NotImplemented
        equality = 0
        for slot in Fitting.slots:
            item_counts = {i.type_id: i.quantity-1 for i in getattr(self, slot)}
            items = Counter([i.type_id for i in getattr(self, slot)])
            items.update(item_counts)
            other_item_counts = {i.type_id: i.quantity-1 for i in getattr(other, slot)}
            other_items = Counter([i.type_id for i in getattr(other, slot)])
            other_items.update(other_item_counts)
            items.subtract(other_items)
            for item, count in items.iteritems():
                if count < 0:
                    return -1
                if count > 0:
                    equality += count
        return equality

    def __str__(self):
        slot_strings = []
        for slot in Fitting.slots:
            slot_strs = [Fitting._name_count(i) for i in getattr(self, slot, {}) if i]
            if slot_strs:
                slot_str = ', '.join(sorted(slot_strs))
                slot_strings.append('{}: {}'.format(slot, slot_str))
        return '\n'.join(sorted(slot_strings))


import sqlite3

from config import CONFIG
from util import esi_api, access_token, name_to_id
from bravado.exception import HTTPNotFound, HTTPForbidden


class Fitting(object):
    """docstring for Fitting"""
    def __init__(self, Cargo=[], DroneBay=[], FighterBay=[], FighterTube=[], HiSlot=[], LoSlot=[], MedSlot=[], RigSlot=[], ServiceSlot=[], SubSystemSlot=[]):
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
        slots = ['Cargo', 'DroneBay', 'FighterBay', 'FighterTube', 'HiSlot', 'LoSlot', 'MedSlot', 'RigSlot', 'ServiceSlot', 'SubSystemSlot']
        fittings = {slot: [] for slot in slots}
        fit = False
        for asset in assets:
            flag = asset.get('location_flag')
            if not flag:
                continue
            for slot in slots:
                if flag.startswith(slot):
                    fittings[slot].append(asset)
                    fit = True
        if fit:
            return cls(**fittings)
        return None

    def __str__(self):
        slots = ['Cargo', 'DroneBay', 'FighterBay', 'FighterTube', 'HiSlot', 'LoSlot', 'MedSlot', 'RigSlot', 'ServiceSlot', 'SubSystemSlot']
        slot_strings = []
        for slot in slots:
            slot_strs = [i.get('typeName') for i in getattr(self, slot, {}) if i]
            if slot_strs:
                slot_str = ', '.join(sorted(slot_strs))
                slot_strings.append('{}: {}'.format(slot, slot_str))
        return '\n'.join(sorted(slot_strings))


class CorpAssets(object):
    """docstring for CorpAssets"""
    def __init__(self, corp_id):
        super(CorpAssets, self).__init__()
        self.corp_id = corp_id
        self.assets = {}
        self.asset_tree = {}
        self.locations = {}
        self.structures = {}
        self.stations = {}
        self.types = {}
        type_annotation = {}
        self.categories = {}
        assets_api = esi_api('Assets.get_corporations_corporation_id_assets', token=access_token, corporation_id=corp_id)
        conn = sqlite3.connect('sqlite-latest.sqlite')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        type_ids = set([asset['type_id'] for asset in assets_api])
        param_holder = ','.join('?'*len(type_ids))
        query = """select * from invTypes as i \
                join invGroups as g on i.groupID=g.groupID \
                join invCategories as c on g.categoryID=c.categoryID \
                where i.typeID in ({})""".format(param_holder)
        # builds a category/group/type tree for easier filtering later on
        for row in cur.execute(query, tuple(type_ids)):
            type_dict = dict(row)
            category = self.categories.setdefault(type_dict['categoryID'], {})
            category['categoryName'] = type_dict['categoryName']
            group = category.setdefault(type_dict['groupID'], {})
            group['groupName'] = type_dict['groupName']
            group['typeID'] = type_dict
            self.types[type_dict['typeID']] = type_dict
            type_annotation[type_dict['typeID']] = type_dict.copy()
        # annotates asset with SDE info and indexes by item id
        for asset in assets_api:
            asset.update(type_annotation[asset['type_id']])
            self.assets[asset['item_id']] = asset
            type_entry = self.types[asset['type_id']].setdefault('children', [])
            type_entry.append(asset)
        # build a location tree
        for item_id, asset in self.assets.iteritems():
            location_id = asset['location_id']
            parent = None
            try:
                parent = self.assets[location_id]
            except KeyError:
                # Solar System
                if location_id >= 30000000 and location_id < 32000000:
                    parent = self.asset_tree.setdefault(location_id, {})
                # Stations/Outposts
                if location_id >= 60000000 and location_id < 64000000:
                    try:
                        parent = self.stations[location_id]
                    except KeyError:
                        station = esi_api('Universe.get_universe_stations_station_id', station_id=location_id)
                        system = self.asset_tree.setdefault(station['system_id'], {})
                        station['parent'] = system
                        parent = station
                        self.stations[location_id] = station
                # Probably a structure
                if location_id >= 1000000000000:
                    try:
                        parent = self.structures[location_id]
                    except KeyError:
                        # Someone elses structure?
                        try:
                            structure = esi_api('Universe.get_universe_structures_structure_id', structure_id=location_id, token=access_token)
                            system = self.asset_tree.setdefault(structure['solar_system_id'], {})
                            structure['parent'] = system
                            parent = structure
                            self.structures[location_id] = structure
                        # No access or doesn't exist    
                        except (HTTPForbidden, HTTPNotFound):
                            parent = self.asset_tree.setdefault(location_id, {})
            parent.setdefault('children', []).append(asset)

import datetime
import pytz
import sqlite3
from bravado.exception import HTTPForbidden

from config import CONFIG
from util import esi_api, access_token, name_to_id, ids_to_names
from assets import Fitting


class Structure(object):
    """docstring for Structure"""
    def __init__(self, structure_id, structure_type_id=None, structure_type_name=None, token=access_token, system_id=None, services=None, fuel_expires=None, fitting=None):
        super(Structure, self).__init__()
        self.structure_id = structure_id
        self.structure_type_id = structure_type_id
        self.structure_type_name = structure_type_name
        self.system_id = system_id
        self.fitting = fitting
        self._fuel_rate = 0
        # Grab structure name
        try:
            self.structure_info = esi_api('Universe.get_universe_structures_structure_id', token=access_token, structure_id=structure_id)
            self.name = self.structure_info.get('name')
            self.accessible = True
        except HTTPForbidden, e:
            self.name = "Inaccessible Structure"
            self.accessible = False
        self.online_services = []
        self.offline_services = []
        if services:
            for service in services:
                if service['state'] == 'online':
                    self.online_services.append(service.get('name'))
                if service['state'] == 'offline':
                    self.offline_services.append(service.get('name'))
        self.fuel_expires = fuel_expires

    @property
    def fuel_rate(self):
        if self._fuel_rate:
            return self._fuel_rate
        if not self.fitting:
            return self._fuel_rate
        fuel_bonus = {
            # Raitaru
            35825: {
                # Structure Engineering Service Module
                1415:0.75
            },
            # Azbel
            35826: {
                # Structure Engineering Service Module
                1415:0.75
            },
            # Sotiyo
            35827: {
                # Structure Engineering Service Module
                1415:0.75
            },
            # Athanor
            35835: {
                # Structure Resource Processing Service Module
                1322:0.80
            },
            # Tatara
            35836: {
                # Structure Resource Processing Service Module
                1322:0.75
            },
            # Astrahus
            35832: {
                # Structure Citadel Service Module
                1321:0.75
            },
            # Fortizar
            35833: {
                # Structure Citadel Service Module
                1321:0.75
            },
            # Keepstar
            35834: {
                # Structure Citadel Service Module
                1321:0.75
            }
        }
        template = ','.join('?'*len(self.fitting.ServiceSlot))
        conn = sqlite3.connect('sqlite-latest.sqlite')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        param_holder = ','.join('?'*len(self.fitting.ServiceSlot))
        query = 'select typeID,valueFloat from dgmTypeAttributes where attributeID=2109 and typeID in ({})'.format(param_holder)
        fuel = {}
        for row in cur.execute(query, [s['typeID'] for s in self.fitting.ServiceSlot]):
            fuel[row['typeID']] = row['valueFloat']
        for module in self.fitting.ServiceSlot:
            gid = module['groupID']
            fuel_count = fuel[module['typeID']]
            modifier = 1.0
            if gid in fuel_bonus[self.structure_type_id]:
                modifier = fuel_bonus[self.structure_type_id][gid]
            self._fuel_rate += fuel_count*modifier
        return self._fuel_rate

    @classmethod
    def from_corporation(cls, corporation_name, token=access_token, assets={}):
        corporation_id = name_to_id(corporation_name, 'corporation')
        structures = esi_api('Corporation.get_corporations_corporation_id_structures', token=token, corporation_id=corporation_id)
        structure_keys = ['structure_id', 'system_id', 'services', 'fuel_expires']
        
        for s in structures:
            sid = s['structure_id']
            kwargs = {k:v for k,v in s.items() if k in structure_keys}
            kwargs['token'] = token
            if 'children' in assets.get(sid).keys():
                kwargs['fitting'] = Fitting.from_assets(assets[sid]['children'])
                kwargs['structure_type_id'] = assets[sid]['typeID']
                kwargs['structure_type_name'] = assets[sid]['typeName']
            else:
                kwargs['structure_type_id'] = s['type_id']
                kwargs['structure_type_name'] = ids_to_names([s['type_id']])[s['type_id']]
            yield cls(**kwargs)

    def __str__(self):
        return '{} ({}) - {}'.format(self.name, self.structure_id, self.structure_type_name)


def check_citadels():
    """
    Check citadels for fuel and services status
    """
    corporation_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    structures = esi_api('Corporation.get_corporations_corporation_id_structures', token=access_token, corporation_id=corporation_id)
    detonations = esi_api('Industry.get_corporation_corporation_id_mining_extractions', token=access_token, corporation_id=corporation_id)
    detonations = {d['structure_id']: d for d in detonations}
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    too_soon = datetime.timedelta(days=CONFIG['TOO_SOON'])
    detonation_warning = datetime.timedelta(days=CONFIG['DETONATION_WARNING'])
    messages = []
    for structure in structures:
        structure_id = structure['structure_id']
        message = []

        # Grab structure name
        try:
            structure_info = esi_api('Universe.get_universe_structures_structure_id', token=access_token, structure_id=structure_id)
        except HTTPForbidden, e:
            messages.append('Found a citadel ({}) in {} that doesn\'t allow {} to dock!'.format(structure_id,
                                                                                                structure['system_id'],
                                                                                                CONFIG['CORPORATION_NAME']))
            continue
        name = structure_info.get('name')

        # List online/offline services
        online_services = []
        offline_services = []
        for service in structure.get('services') or []:
            if service['state'] == 'online':
                online_services.append(service.get('name'))
                if service['name'] == 'Moon Drilling' and not detonations.get(structure_id):
                    message.append('Needs to have an extraction scheduled')
            if service['state'] == 'offline':
                offline_services.append(service.get('name'))
        online = ', '.join([service for service in online_services])
        offline = ', '.join([service for service in offline_services])

        # Check when fuel expires
        fuel_expires = structure.get('fuel_expires', None)

        # Check for upcoming detonations
        try:
            detonation = detonations[structure_id]['chunk_arrival_time']
            if detonation - now < detonation_warning:
                message.append('Ready to detonate {}'.format(detonation))
        except KeyError:
            pass

        # Build message for fuel running out and offline services 
        if fuel_expires and (fuel_expires - now < too_soon):
            message.append('Runs out of fuel on {}'.format(fuel_expires))
            if online_services:
                message.append('Online Services: {}'.format(online))
            if offline_services:
                message.append('Offline Services: {}'.format(offline))
        elif offline_services:
            message.append('Offline services: {}'.format(offline))
        if message:
            messages.append('\n'.join(['{}'.format(name)] + message))
    return messages

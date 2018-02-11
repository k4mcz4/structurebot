import datetime
import pytz
import sqlite3

from config import CONFIG
from util import esi, esi_client, name_to_id, ids_to_names
from assets import Fitting, CorpAssets


class Structure(object):
    def __init__(self, structure_id, type_id=None, type_name=None, system_id=None, services=None, fuel_expires=None, fitting=Fitting()):
        super(Structure, self).__init__()
        self.structure_id = structure_id
        self.type_id = type_id
        self.type_name = type_name
        self.system_id = system_id
        self.fitting = fitting
        self._fuel_rate = 0
        # Grab structure name
        structure_request = esi.op['get_universe_structures_structure_id'](structure_id=structure_id)
        structure_response = esi_client.request(structure_request)
        if structure_response.status == 200:
            structure_info = structure_response.data
            self.name = structure_info.get('name')
            self.system_id = structure_info.get('system_id')
            self.type_id = structure_info.get('type_id')
            self.accessible = True
        elif structure_response.status == 403:
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
            if gid in fuel_bonus[self.type_id]:
                modifier = fuel_bonus[self.type_id][gid]
            self._fuel_rate += fuel_count*modifier
        return self._fuel_rate

    @classmethod
    def from_corporation(cls, corporation_name, assets=None):
        corporation_id = name_to_id(corporation_name, 'corporation')
        if not assets:
            assets = CorpAssets(corporation_id).assets
        structures_request = esi.op['get_corporations_corporation_id_structures'](corporation_id=corporation_id)
        structures_response = esi_client.request(structures_request)
        structures = structures_response.data
        structure_keys = ['structure_id', 'system_id', 'services', 'fuel_expires']
        
        for s in structures:
            sid = s['structure_id']
            kwargs = {k:v for k,v in s.items() if k in structure_keys}
            if 'children' in assets.get(sid, {}).keys():
                kwargs['fitting'] = Fitting.from_assets(assets[sid]['children'])
                kwargs['type_id'] = assets[sid]['typeID']
                kwargs['type_name'] = assets[sid]['typeName']
            else:
                kwargs['type_id'] = s['type_id']
                kwargs['type_name'] = ids_to_names([s['type_id']])[s['type_id']]
            yield cls(**kwargs)

    def __str__(self):
        return '{} ({}) - {}'.format(self.name, self.structure_id, self.type_name)


def check_citadels():
    """
    Check citadels for fuel and services status
    
    Returns:
        list: list of alert strings

    >>> set([type(s) for s in check_citadels()])
    set([<type 'str'>])
    """
    corporation_id = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    structures_request = esi.op['get_corporations_corporation_id_structures'](corporation_id=corporation_id)
    structures_response = esi_client.request(structures_request)
    structures = structures_response.data
    detonations_request = esi.op['get_corporation_corporation_id_mining_extractions'](corporation_id=corporation_id)
    detonations_response = esi_client.request(detonations_request)
    detonations = detonations_response.data
    detonations = {d['structure_id']: d for d in detonations}
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    too_soon = datetime.timedelta(days=CONFIG['TOO_SOON'])
    detonation_warning = datetime.timedelta(days=CONFIG['DETONATION_WARNING'])
    messages = []
    for structure in structures:
        structure_id = structure['structure_id']
        message = []

        # Grab structure name
        structure_request = esi.op['get_universe_structures_structure_id'](structure_id=structure_id)
        structure_response = esi_client.request(structure_request)
        if structure_response.status in [403, 404]:
            messages.append('Found a citadel ({}) in {} that doesn\'t allow {} to dock!'.format(structure_id,
                                                                                                structure['system_id'],
                                                                                                CONFIG['CORPORATION_NAME']))
            continue
        structure_info = structure_response.data
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
            if detonation.v - now < detonation_warning:
                message.append('Ready to detonate {}'.format(detonation))
        except KeyError:
            pass

        # Build message for fuel running out and offline services 
        if fuel_expires and (fuel_expires.v - now < too_soon):
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

if __name__ == '__main__':
    check_citadels()
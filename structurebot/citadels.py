import datetime
import pytz

from config import CONFIG
from util import esi, esi_client, name_to_id, ids_to_names
from assets import Fitting, Asset


class Structure(object):
    def __init__(self, structure_id, type_id=None, type_name=None,
                 system_id=None, services=None, fuel_expires=None,
                 accessible=None, name=None, detonation=None,
                 fitting=Fitting()):
        super(Structure, self).__init__()
        self.structure_id = structure_id
        self.type_id = type_id
        self.type_name = type_name
        self.system_id = system_id
        self.fuel_expires = fuel_expires
        self.accessible = accessible
        self.name = name
        self.detonation = detonation
        self.fitting = fitting
        self._fuel_rate = 0
        # Grab structure name
        endpoint = 'get_universe_structures_structure_id'
        structure_request = esi.op[endpoint](structure_id=structure_id)
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
                1415: 0.75
            },
            # Azbel
            35826: {
                # Structure Engineering Service Module
                1415: 0.75
            },
            # Sotiyo
            35827: {
                # Structure Engineering Service Module
                1415: 0.75
            },
            # Athanor
            35835: {
                # Structure Resource Processing Service Module
                1322: 0.80
            },
            # Tatara
            35836: {
                # Structure Resource Processing Service Module
                1322: 0.75
            },
            # Astrahus
            35832: {
                # Structure Citadel Service Module
                1321: 0.75
            },
            # Fortizar
            35833: {
                # Structure Citadel Service Module
                1321: 0.75
            },
            # 'Moreau' Fortizar
            47512: {
                # Structure Citadel Service Module
                1321: 0.65,
                # Structure Engineering Service Module
                1415: 0.65,
                # Structure Resource Processing Service Module
                1322: 0.65                
            },
            # 'Draccous' Fortizar
            47513: {
                # Structure Citadel Service Module
                1321: 0.75,
                # Structure Engineering Service Module
                1415: 0.75
            },
            # 'Horizon' Fortizar
            47514: {
                # Structure Citadel Service Module
                1321: 0.75,
                # Structure Engineering Service Module
                1415: 0.75
            },
            # 'Marginis' Fortizar
            47515: {
                # Structure Citadel Service Module
                1321: 0.50,
                # Structure Engineering Service Module
                1415: 0.50,
                # Structure Resource Processing Service Module
                1322: 0.50
            },
            # 'Prometheus' Fortizar
            47516: {
                # Structure Citadel Service Module
                1321: 0.75,
                # Structure Resource Processing Service Module
                1322: 0.75                
            },
            # Keepstar
            35834: {
                # Structure Citadel Service Module
                1321: 0.75
            }
        }
        service_fuel_usage = {}
        for service in self.fitting.ServiceSlot:
            hourly_fuel = [a.value for a in service.dogma_attributes if a.attribute_id == 2109][0]
            try:
                if service.group_id in fuel_bonus[self.type_id]:
                    modifier = fuel_bonus[self.type_id][service.group_id]
                else:
                    modifier = 1.0
            except KeyError:
                modifier = 1.0
            self._fuel_rate += hourly_fuel*modifier
        return self._fuel_rate

    @classmethod
    def from_corporation(cls, corporation_name, assets=None):
        structure_list = []
        corporation_id = name_to_id(corporation_name, 'corporation')
        assets = assets or Asset.from_id(corporation_id, 'corporations')
        endpoint = 'get_corporations_corporation_id_structures'
        structures_request = esi.op[endpoint](corporation_id=corporation_id)
        structures_response = esi_client.request(structures_request)
        structures = structures_response.data
        endpoint = 'get_corporation_corporation_id_mining_extractions'
        detonations_request = esi.op[endpoint](corporation_id=corporation_id)
        detonations_response = esi_client.request(detonations_request)
        detonations = detonations_response.data
        detonations = {d['structure_id']: d['chunk_arrival_time']
                       for d in detonations}
        structure_keys = ['structure_id', 'system_id',
                          'services', 'fuel_expires']
        for s in structures:
            sid = s['structure_id']
            kwargs = {k: v for k, v in s.items() if k in structure_keys}
            kwargs['type_id'] = s['type_id']
            kwargs['type_name'] = ids_to_names([s['type_id']])[s['type_id']]
            kwargs['detonation'] = detonations.get(sid)
            structure_contents = [a for a in assets if a.location_id == sid]
            if structure_contents:
                kwargs['fitting'] = Fitting.from_assets(structure_contents)
            structure_list.append(cls(**kwargs))
        return structure_list

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'{} ({}) - {}'.format(self.name, self.structure_id,
                                     self.type_name)


def check_citadels(corp_name, corp_assets=None):
    """
    Check citadels for fuel and services status

    Returns:
        list: list of alert strings

    >>> set([type(s) for s in check_citadels(CONFIG['CORPORATION_NAME'])])
    set([<type 'unicode'>])
    """
    structures = Structure.from_corporation(corp_name, corp_assets)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    too_soon = datetime.timedelta(days=CONFIG['TOO_SOON'])
    detonation_warning = datetime.timedelta(days=CONFIG['DETONATION_WARNING'])
    messages = []
    for structure in structures:
        sid = structure.structure_id
        sysid = structure.system_id
        online = structure.online_services
        offline = structure.offline_services
        message = []
        if not structure.accessible:
            msg = 'Found an inaccesible citadel ({}) in {}'.format(sid, sysid)
            messages.append(msg)
            continue
        for service in online:
            if service == 'Moon Drilling' and not structure.detonation:
                message.append('Needs to have an extraction scheduled')

        # Check for upcoming detonations
        # TODO: yell at pyswagger.  Why is the actual datetime in an attribute?
        detonation = structure.detonation
        if detonation and (detonation.v - now < detonation_warning):
            message.append('Ready to detonate {}'.format(structure.detonation))

        # Build message for fuel running out and offline services
        fuel_expires = structure.fuel_expires
        if fuel_expires and (fuel_expires.v - now < too_soon):
            message.append('Runs out of fuel on {}'.format(fuel_expires))
            if online:
                message.append('Online Services: {}'.format(', '.join(online)))
            if offline:
                message.append('Offline Services: {}'.format(', '.join(offline)))
        elif offline:
            message.append('Offline services: {}'.format(', '.join(offline)))
        if message:
            messages.append(u'\n'.join([u'{}'.format(structure.name)] + message))
    return messages

if __name__ == '__main__':
    check_citadels()

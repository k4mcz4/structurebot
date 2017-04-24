
from config import *
from util import xml_api
from util import pprinter
from pos_resources import pos_fuel, moon_goo

def corp_assets(xml_client, corp_id=CORPORATION_ID):
    asset_xml = xml_api(xml_client, '/corp/AssetList.xml.aspx', params={'corporationID': corp_id})
    print(ET.tostring(asset_xml))
    return asset_xml

def item_locations(xml_client, ids):
    locations_xml = xml_api(xml_client, '/corp/Locations.xml.aspx', params={'ids': ','.join(str(id) for id in ids)}, xpath='.//rowset[@name="locations"]/row')
    location_dict = {}
    for location in locations_xml:
        location_dict[location.get('itemID')] = {k: location.attrib[k] for k in ['itemName', 'x', 'y', 'z']}
    return location_dict

def sov_systems(esi_client, sov_holder):
    sov_holder_id = esi_client.Search.get_search(categories=['alliance'], search=sov_holder, strict=True).result().get('alliance')[0]
    map_sov = esi_client.Sovereignty.get_sovereignty_map().result()
    sov_systems = []
    for system in map_sov:
        try:
            if system['alliance_id'] == sov_holder_id:
                sov_systems.append(system['system_id'])
        except KeyError:
            continue
    return sov_systems
 
def check_pos(xml_client, esi_client):
    pos_list_xml = xml_api(xml_client, '/corp/StarbaseList.xml.aspx')
    poses = {}
    messages = []
    sovs = sov_systems(esi_client, SOV_HOLDER)
    for pos in pos_list_xml.findall('.//rowset[@name="starbases"]/row'):
        pos_id = int(pos.get('itemID'))
        type_id = int(pos.get('typeID'))
        location_id = int(pos.get('locationID'))
        location_name = esi_client.Universe.get_universe_systems_system_id(system_id=location_id).result().get('name')
        moon_id = int(pos.get('moonID'))
        moon_name = esi_client.Universe.get_universe_moons_moon_id(moon_id=moon_id).result().get('name')
        sov = location_id in sovs
        poses[pos_id] = poses.get(pos_id, {'type': type_id, 'location_id': location_id, 'location_name': location_name, 'moon_name': moon_name, 'moon_id': moon_id, 'fuel': {}, 'stront': {}, 'silos': {}})
        pos_fuel_xml = xml_api(xml_client, '/corp/StarbaseDetail.xml.aspx', params={'itemID': pos_id }, xpath='.//rowset[@name="fuel"]/row')
        for fuel in pos_fuel_xml:
            fuel_type_id = int(fuel.get('typeID'))
            quantity = int(fuel.get('quantity'))
            multiplier = .75 if sov else 1.0
            rate = pos_fuel[type_id][fuel_type_id]['quantity'] * multiplier
            if fuel_type_id == 16275:
                reinforce_hours = int(quantity / rate)
                if reinforce_hours < STRONT_HOURS:
                    messages.append("{} has only {} hours of stront".format(moon_name, reinforce_hours))
                poses[pos_id]['stront'] = {'quantity': quantity, 'hourly_rate': rate}
            else:
                how_soon = int(quantity / (rate*24))
                if how_soon < TOO_SOON:
                    messages.append("{} will run out of fuel in {} days".format(moon_name, how_soon))
                poses[pos_id]['fuel'][fuel_type_id] = {'quantity': quantity, 'rate': rate}
    locations = item_locations(xml_client, poses.keys())
    return messages
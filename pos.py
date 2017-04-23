
from config import *
from util import xml_api

from util import pprinter

def corp_assets(xml_client, corp_id=CORPORATION_ID):
    asset_xml = xml_api(xml_client, '/corp/AssetList.xml.aspx', params={'corporationID': corp_id})
    print(ET.tostring(asset_xml))
    return asset_xml

def item_locations(xml_client, ids):
    locations_xml = xml_api(xml_client, '/corp/Locations.xml.aspx', params={'ids': ','.join(ids)}, xpath='.//rowset[@name="locations"]/row')
    location_dict = {}
    for location in locations_xml:
        location_dict[location.get('itemID')] = {k: location.attrib[k] for k in ['itemName', 'x', 'y', 'z']}
    print location_dict
    return location_dict
   
def check_pos(xml_client, esi_client):
    pos_list_xml = xml_api(xml_client, '/corp/StarbaseList.xml.aspx')
    poses = {}
    for pos in pos_list_xml.findall('.//rowset[@name="starbases"]/row'):
        pos_id = pos.get('itemID')
        poses[pos_id] = poses.get(pos_id, {'type': pos.get('typeID'), 'fuel': {}, 'silos': {}})
        pos_fuel_xml = xml_api(xml_client, '/corp/StarbaseDetail.xml.aspx', params={'itemID': pos_id }, xpath='.//rowset[@name="fuel"]/row')
        for fuel in pos_fuel_xml:
            poses[pos_id]['fuel'][fuel.get('typeID')] = fuel.get('quantity')
    locations = item_locations(xml_client, poses.keys())
    pprinter.pprint(poses)
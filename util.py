import requests
from xml.etree import cElementTree as ET
from pprint import PrettyPrinter

pprinter = PrettyPrinter()

def get_access_token(refresh, client_id, client_secret):
    """
    Grab API access token using refresh token
    """
    params = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh
    }
    token_response = requests.post('https://login.eveonline.com/oauth/token', data=params, auth=(client_id, client_secret))
    token_response.raise_for_status()
    return token_response.json()['access_token']

def xml_api(xml_client, endpoint, xpath=None, params=None):
    """
    Accesses CCP XML api in a useful way and returns ET root
    """
    xml_response = xml_client.get('https://api.eveonline.com' + endpoint, params=params)
    xml_root = ET.fromstring(xml_response.content)
    try:
        xml_response.raise_for_status()
    except requests.HTTPError, e:
        xml_error = xml_root.find('.//error')
        message = "Error code {}: {}".format(xml_error.get('code'), xml_error.text)
        e.args = (message,)
        raise e
    if xpath:
        xml = xml_root.findall(xpath)
    else:
        xml = xml_root
    return xml
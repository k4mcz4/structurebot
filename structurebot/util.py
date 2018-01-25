import requests
import time
from operator import attrgetter
from esipy import App, EsiClient, EsiSecurity
from xml.etree import cElementTree as ET
from pprint import PrettyPrinter

from config import *

pprinter = PrettyPrinter()

esi_path = os.path.abspath(__file__)
esi_dir_path = os.path.dirname(esi_path)

esi = App.create(esi_dir_path + '/esi.json')

esi_security = EsiSecurity(
    app=esi,
    redirect_uri='http://localhost',
    client_id=CONFIG['SSO_APP_ID'],
    secret_key=CONFIG['SSO_APP_KEY'],
)

esi_security.update_token({
    'access_token': '',
    'expires_in': -1,
    'refresh_token': CONFIG['SSO_REFRESH_TOKEN']
})

esi_client = EsiClient(
    retry_requests=True, 
    header={'User-Agent': 'https://github.com/eve-n0rman/structurebot'},
    raw_body_only=False,
    security=esi_security
)

def name_to_id(name, name_type):
    """Looks up a name of name_type in ESI
    
    Args:
        name (string): Name to search for
        name_type (string): types to search (see ESI for valid types)
    
    Returns:
        integer: eve ID or None if no match

    >>> name_to_id('Aunsou', 'solar_system')
    30003801
    >>> name_to_id('n0rman', 'character')
    1073945516
    >>> name_to_id('Nonexistent', 'solar_system')
    """
    get_search = esi.op['get_search'](categories=[name_type],
                                   search=name,
                                  strict=True)
    response = esi_client.request(get_search)
    try:
        return getattr(response.data, name_type)[0]
    except KeyError:
        return None


def ids_to_names(ids):
    """Looks up names from a list of ids
    
    Args:
        ids (list of integers): list of ids to resolve to names
    
    Returns:
        dict: dict of id to name mappings

    >>> ids_to_names([1073945516, 30003801])
    {30003801: u'Aunsou', 1073945516: u'n0rman'}
    >>> ids_to_names([1])
    Traceback (most recent call last):
    ...
    HTTPError: Ensure all IDs are valid before resolving.
    """
    id_name = {}
    chunk_size = 999
    for chunk in [ids[i:i + chunk_size] for i in xrange(0, len(ids), chunk_size)]:
        post_universe_names = esi.op['post_universe_names'](ids=chunk)
        response = esi_client.request(post_universe_names)
        if response.status == 200:
            id_name.update({i.id: i.name for i in response.data})
        elif response.status == 404:
            raise requests.exceptions.HTTPError(response.data['error'])
    return id_name


def annotate_element(row, dict):
    """Sets attributes on an Element from a dict
    
    Args:
        row (TYPE): Description
        dict (TYPE): Description
    """
    for key, value in dict.iteritems():
        row[key] = str(value)


def notify_slack(messages):
    params = {
        'text': '\n\n'.join(messages)
    }
    if CONFIG['SLACK_CHANNEL']:
        params['channel'] = CONFIG['SLACK_CHANNEL']
    results = requests.post(CONFIG['OUTBOUND_WEBHOOK'], json=params)
    results.raise_for_status()
    print params

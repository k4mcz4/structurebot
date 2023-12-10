from __future__ import absolute_import
from __future__ import print_function
import json
import requests
from requests.exceptions import HTTPError
# import time
import logging
#from urllib.parse import urlparse
# from operator import attrgetter
#from esipy import App, EsiApp, EsiClient, EsiSecurity
#from esipy.cache import DictCache
# from pyswagger.primitives import MimeCodec
# from pyswagger.primitives.codec import PlainCodec

from .config import *


from .neucore_requester import NCR

logger = logging.getLogger(__name__)


#def setup_esi(neucore_host, neucore_app_token, neucore_datasource, user_agent, cache=DictCache()):
"""Set up the ESI client

    Args:
        neucore_host (string): Neucore host
        neucore_app_token (string): Neucore app auth token
        neucore_datasource (string): Data source parameter for Neucore ESI requests
        user_agent (string): The HTTP user agent
        cache (False, optional): esipy.cache instance

    Returns:
        tuple: esi app definition, esi client

    >>> setup_esi(CONFIG['NEUCORE_HOST'], CONFIG['NEUCORE_APP_TOKEN'], CONFIG['NEUCORE_DATASOURCE'],
    ...           CONFIG['USER_AGENT'], cache) # doctest: +ELLIPSIS
    (<pyswagger.core.App object ...>, <pyswagger.core.App object ...>, '...', <esipy.client.EsiClient object ...>)
    """

"""
    esi_meta = EsiApp(cache=cache)
    esi_public = esi_meta.get_latest_swagger

    # Get, adjust and write OpenAPI definition file for the Neucore ESI proxy
    core_swagger_file = os.path.dirname(os.path.abspath(__file__)) + '/latest_swagger_core.json'
    swagger = requests.get('https://esi.evetech.net/latest/swagger.json')
    swagger_data = swagger.json()
    swagger_data['basePath'] = '/api/app/v2/esi/latest'
    swagger_data['host'] = neucore_host
    del swagger_data['parameters']['datasource']['enum']
    with open(core_swagger_file, 'w') as f:
        json.dump(swagger_data, f)
    esi_authenticated = App.create(core_swagger_file)
    datasource = neucore_datasource

    esi_security = EsiSecurity(
        redirect_uri='http://localhost',
        client_id="",
        secret_key="",
        headers={'User-Agent': user_agent}
    )

    # Add Neucore token that expires far in the future
    esi_security.update_token({
        'access_token': neucore_app_token,
        'expires_in': 9000,  # 150 minutes
        'refresh_token': ''
    })

    client = EsiClient(
        retry_requests=True,
        headers={'User-Agent': user_agent},
        raw_body_only=False,
        security=esi_security,
        cache=cache
    )

    return esi_public, esi_authenticated, datasource, client
"""


#esi_pub, esi_auth, esi_datasource, esi_client = setup_esi(CONFIG['NEUCORE_HOST'], CONFIG['NEUCORE_APP_TOKEN'], CONFIG['NEUCORE_DATASOURCE'], CONFIG['USER_AGENT'])

# TODO Enable cache in production environment or add config variables

ncr = NCR(app_id=CONFIG['NEUCORE_APP_ID'],
          app_secret=CONFIG['NEUCORE_APP_SECRET'],
          neucore_prefix=CONFIG['NEUCORE_HOST'],
          datasource=CONFIG['NEUCORE_DATASOURCE'],
          useragent=CONFIG['USER_AGENT'],
          cache_esi=False,
          cache_nc=False)


############

cat_name_id = {} # stores name:id pairs by category to save on requests
id_namecat = {} # stores (name,category) by ID to save on requests


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

    if name_type == 'corporation':
        category = 'corporations'
    elif name_type == 'inventory_type':
        category = 'inventory_types'
    elif name_type == 'solar_system':
        category = 'systems'
    elif name_type == 'character':
        category = 'characters'
    else:
        return None
    try:
        return cat_name_id[category][name]
    except KeyError:
        # data not found in cache
        pass
    # try fetch ID
    try:
        names_to_ids([name])
    except HTTPError:
        return None
    try:
        return cat_name_id[category][name]
    except KeyError:
        # data not found after fetching
        return None
    

def names_to_ids(lookup_names):

    """
    Resolve a set of names to IDs in the following categories:
        agents, alliances, characters, constellations, corporations,
        factions, inventory_types, regions, stations, and systems.
    Only exact matches will be returned. All names searched for are cached for 12 hours
    """
    names = []
    name_id = {}

    for n in lookup_names:
        found = False
        for c in cat_name_id.keys():
            if n in cat_name_id[c].keys():
                found=True
                name_id[name] = cat_name_id[c][n]
                break
        if not found:
            names.append(n)
        
    if len(names)>0:
        chunk_size = 400 # Max Items is 500
        for chunk in [names[i:i+ chunk_size] for i in range(0,len(names),chunk_size)]:
            resp, chunk_data = ncr.post_universe_ids(ids=chunk)
            if resp.status_code == 200:
                for category in chunk_data.keys():
                    if not category in cat_name_id.keys():
                        cat_name_id[category] = {}
                    for name in chunk_data[category].keys():
                        cat_name_id[category][name]=chunk_data[category][name]
                        id_namecat[chunk_data[category][name]]=(name,category)
                        name_id[name]=chunk_data[category][name] 
    return name_id

def ids_to_names(lookup_ids):
    """Looks up names from a list of ids

    Args:
        ids (list of integers): list of ids to resolve to names

    Returns:
        dict: dict of id to name mappings

    >>> ids_to_names([1073945516, 30003801])
    {30003801: 'Aunsou', 1073945516: 'n0rman'}
    >>> ids_to_names([1])
    Traceback (most recent call last):
    ...
    requests.exceptions.HTTPError: Ensure all IDs are valid before resolving.
    """
    ids = []
    id_name = {}
    for i in lookup_ids :
        try:
            id_name[i]=id_namecat[i][0]
        except KeyError:
            ids.append(i)
    if(len(ids)>0):
        chunk_size = 400 # max is 500
        for chunk in [ids[i:i + chunk_size] for i in range(0, len(ids), chunk_size)]:
            resp, chunk_data = ncr.post_universe_names(names=chunk)
            if resp.status_code == 200:
                for d in chunk_data:
                    d_id=d["id"]
                    d_cat=d["category"]
                    d_name=d["name"]
                    id_namecat[d_id]=(d_name,d_cat)
                    if not d_cat in cat_name_id.keys():
                        cat_name_id[d_cat]={}
                    cat_name_id[d_cat][d_name]=d_id
                    id_name[d_id]=d_name
    
            
    return dict(sorted(id_name.items()))

############


def notify_slack(messages):
    params = {
        'text': '\n\n'.join(messages)
    }
    results = requests.post(CONFIG['OUTBOUND_WEBHOOK'], json=params)
    results.raise_for_status()
    # print(params)




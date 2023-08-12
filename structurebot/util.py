from __future__ import absolute_import
from __future__ import print_function
import json
import requests
from requests.exceptions import HTTPError
# import time
import logging
from six.moves.urllib.parse import urlparse
# from operator import attrgetter
from esipy import App, EsiApp, EsiClient, EsiSecurity
from esipy.cache import DictCache
# from pyswagger.primitives import MimeCodec
# from pyswagger.primitives.codec import PlainCodec

from .config import *
import six
from six.moves import range

logger = logging.getLogger(__name__)


def config_esi_cache(cache_url):
    """Configure ESI cache backend

    Args:
        cache_url (string): diskcache or redis url

    Returns:
        cache: esipy.cache

    >>> config_esi_cache('diskcache:/tmp/esipy-diskcache') # doctest: +ELLIPSIS
    <esipy.cache.FileCache object at 0x...>
    >>> config_esi_cache('redis://user:password@127.0.0.1:6379/') # doctest: +ELLIPSIS
    <esipy.cache.RedisCache object at 0x...>
    """
    cache = DictCache()
    if cache_url:
        cache_url = urlparse(cache_url)
        if cache_url.scheme == 'diskcache':
            from esipy.cache import FileCache
            filename = cache_url.path
            cache = FileCache(path=filename)
        elif cache_url.scheme == 'redis':
            from esipy.cache import RedisCache
            import redis
            redis_server = cache_url.hostname
            redis_port = cache_url.port
            redis_client = redis.Redis(host=redis_server, port=redis_port)
            cache = RedisCache(redis_client)
    return cache


def setup_esi(neucore_host, neucore_app_token, neucore_datasource, user_agent, cache=DictCache()):
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

    esi_meta = EsiApp(cache=cache)
    esi_public = esi_meta.get_latest_swagger

    # Get, adjust and write OpenAPI definition file for the Neucore ESI proxy
    core_swagger_file = os.path.dirname(os.path.abspath(__file__)) + '/latest_swagger_core.json'
    swagger = requests.get('https://esi.evetech.net/latest/swagger.json')
    swagger_data = swagger.json()
    swagger_data['basePath'] = '/api/app/v1/esi/latest'
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


cache = config_esi_cache(CONFIG['ESI_CACHE'])
esi_pub, esi_auth, esi_datasource, esi_client = setup_esi(CONFIG['NEUCORE_HOST'], CONFIG['NEUCORE_APP_TOKEN'],
                                                          CONFIG['NEUCORE_DATASOURCE'], CONFIG['USER_AGENT'], cache)


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
    try:
        name_id = names_to_ids([name])
    except HTTPError:
        return None

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
        return name_id[category][name]
    except KeyError:
        return None


def names_to_ids(names):
    """Looks up ids from a list of names and a name type

    Args:
        names (list of strings): list of names to resolve to ids

    Returns:
        dict: dict of name to id mappings

    >>> names_to_ids(['n0rman', 'Aunsou'])
    {'characters': {'n0rman': 1073945516}, 'systems': {'Aunsou': 30003801}}
    >>> names_to_ids(['this is not a real name n0rman'])
    {}
    """
    name_id = {}
    chunk_size = 999
    for chunk in [names[i:i + chunk_size] for i in range(0, len(names), chunk_size)]:
        post_universe_ids = esi_pub.op['post_universe_ids'](names=chunk)
        response = esi_client.request(post_universe_ids)
        if response.status == 200:
            for category, category_names in six.iteritems(response.data):
                name_id[category] = {i.name: i.id for i in category_names}
        else:
            raise HTTPError(response.data['error'])
    return name_id


def ids_to_names(ids):
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
    id_name = {}
    chunk_size = 999
    for chunk in [ids[i:i + chunk_size] for i in range(0, len(ids), chunk_size)]:
        post_universe_names = esi_pub.op['post_universe_names'](ids=chunk)
        response = esi_client.request(post_universe_names)
        if response.status == 200:
            id_name.update({i.id: i.name for i in response.data})
        elif response.status == 404:
            raise HTTPError(response.data['error'])
    return dict(sorted(id_name.items()))


def notify_slack(messages):
    params = {
        'text': '\n\n'.join(messages)
    }
    if CONFIG['SLACK_CHANNEL']:
        params['channel'] = CONFIG['SLACK_CHANNEL']
    results = requests.post(CONFIG['OUTBOUND_WEBHOOK'], json=params)
    results.raise_for_status()
    # print(params)

import requests
from requests.exceptions import HTTPError
import time
import logging
from urlparse import urlparse
from operator import attrgetter
from esipy import EsiApp, EsiClient, EsiSecurity
from esipy.cache import DictCache
from pyswagger.primitives import MimeCodec
from pyswagger.primitives.codec import PlainCodec

from config import *

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


def setup_esi(app_id, app_secret, refresh_token, cache=DictCache()):
    """Set up the ESI client

    Args:
        app_id (string): SSO Application ID from CCP
        app_secret (string): SSO Application Secret from CCP
        refresh_token (string): SSO refresh token
        cache (False, optional): esipy.cache instance

    Returns:
        tuple: esi app definition, esi client

    >>> setup_esi(CONFIG['SSO_APP_ID'], CONFIG['SSO_APP_KEY'],
    ...           CONFIG['SSO_REFRESH_TOKEN'], cache) # doctest: +ELLIPSIS
    (<pyswagger.core.App object ...>, <esipy.client.EsiClient object ...>)
    """
    esi_meta = EsiApp(cache=cache)
    esi = esi_meta.get_latest_swagger

    esi_security = EsiSecurity(
        redirect_uri='http://localhost',
        client_id=app_id,
        secret_key=app_secret,
        headers={'User-Agent': 'https://github.com/eve-n0rman/structurebot'}
    )

    esi_security.update_token({
        'access_token': '',
        'expires_in': -1,
        'refresh_token': refresh_token
    })

    esi_client = EsiClient(
        retry_requests=True,
        headers={'User-Agent': 'https://github.com/eve-n0rman/structurebot'},
        raw_body_only=False,
        security=esi_security,
        cache=cache
    )

    return (esi, esi_client, esi_security)

cache = config_esi_cache(CONFIG['ESI_CACHE'])
esi, esi_client, esi_security = setup_esi(CONFIG['SSO_APP_ID'], CONFIG['SSO_APP_KEY'],
                                          CONFIG['SSO_REFRESH_TOKEN'], cache)


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


def names_to_ids(names):
    """Looks up ids from a list of names and a name type

    Args:
        names (list of strings): list of names to resolve to ids

    Returns:
        dict: dict of name to id mappings

    >>> names_to_ids(['n0rman', 'Aunsou'])
    {u'systems': {u'Aunsou': 30003801}, u'characters': {u'n0rman': 1073945516}}
    >>> names_to_ids(['this is not a real name n0rman'])
    {}
    """
    name_id = {}
    chunk_size = 999
    for chunk in [names[i:i + chunk_size] for i in xrange(0, len(names), chunk_size)]:
        post_universe_ids = esi.op['post_universe_ids'](names=chunk)
        response = esi_client.request(post_universe_ids)
        if response.status == 200:
            for category, category_names in response.data.iteritems():
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
            raise HTTPError(response.data['error'])
    return id_name


def notify_slack(messages):
    params = {
        'text': '\n\n'.join(messages)
    }
    if CONFIG['SLACK_CHANNEL']:
        params['channel'] = CONFIG['SLACK_CHANNEL']
    results = requests.post(CONFIG['OUTBOUND_WEBHOOK'], json=params)
    results.raise_for_status()
    print params

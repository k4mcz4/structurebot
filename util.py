import requests
import time
from operator import attrgetter
from requests.exceptions import HTTPError, Timeout, ConnectionError
from bravado.client import SwaggerClient
from bravado.swagger_model import load_file
from bravado.exception import HTTPServerError, HTTPNotFound, HTTPForbidden, HTTPUnauthorized, HTTPError
from xml.etree import cElementTree as ET
from pprint import PrettyPrinter

from config import *

pprinter = PrettyPrinter()

for retry in range(5):
    try:
        esi_client = SwaggerClient.from_spec(load_file('esi.json'), config={'also_return_response': True})
        xml_client = requests.Session()
        break
    except (HTTPServerError, HTTPNotFound), e:
        if retry < 4:
            print('Attempt #{} - {}'.format(retry, e))
            time.sleep(60)
            continue
        raise

def name_to_id(name, name_type):
    name_id = esi_api('Search.get_search',
                        categories=[name_type],
                        search=name,
                        strict=True).get(name_type)[0]
    return name_id

def get_access_token(refresh, client_id, client_secret):
    """
    Grab API access token using refresh token
    """
    params = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh
    }
    for retry in range(5):
        try:
            token_response = requests.post('https://login.eveonline.com/oauth/token', data=params, auth=(client_id, client_secret))
            token_response.raise_for_status()
        except (HTTPError, Timeout, ConnectionError), e:
            if retry < 4:
                print ('Attempt #{} - {}'.format(retry, e))
                time.sleep(60)
                continue
            raise
    return token_response.json()['access_token']

access_token = get_access_token(CONFIG['SSO_REFRESH_TOKEN'], CONFIG['SSO_APP_ID'], CONFIG['SSO_APP_KEY'])
xml_client.params = {
    'accessToken': access_token,
    'accessType': 'corporation'
}


def annotate_element(row, dict):
    """Sets attributes on an Element from a dict"""
    for key, value in dict.iteritems():
        row[key] = str(value)


def esi_api(endpoint, **kwargs):
    esi_func_finder = attrgetter(endpoint)
    esi_func = esi_func_finder(esi_client)
    result = {}
    for retry in range(5):
        try:
            result, http_response = esi_func(**kwargs).result()
            if http_response.headers.get('warning'):
                message = endpoint + ' - ' + http_response.headers.get('warning')
                raise PendingDeprecationWarning(message)
            return result
        except (HTTPServerError, HTTPNotFound), e:
            if retry < 4:
                print('{} ({}) attempt #{} - {}'.format(endpoint, kwargs, retry+1, e))
                time.sleep(60)
                continue
            e.message = e.message if e.message else e.swagger_result.error
            raise
        except (HTTPForbidden, HTTPUnauthorized), e:
            e.message = e.message if e.message else e.swagger_result.error
            raise


def notify_slack(messages):
    params = {
        'text': '\n\n'.join(messages)
    }
    if CONFIG['SLACK_CHANNEL']:
        params['channel'] = CONFIG['SLACK_CHANNEL']
    results = requests.post(CONFIG['OUTBOUND_WEBHOOK'], json=params)
    results.raise_for_status()
    print params
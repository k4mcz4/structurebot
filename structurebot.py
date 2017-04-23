#!/usr/bin/env python

import requests
from bravado.client import SwaggerClient

from config import *
from util import get_access_token
from citadels import check_citadels
from pos import check_pos


if __name__ == '__main__':
    esi_client = SwaggerClient.from_url("https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility")
    xml_client = requests.Session()

    access_token = get_access_token(SSO_REFRESH_TOKEN, SSO_APP_ID, SSO_APP_KEY)

    xml_client.params = {
        'accessToken': access_token,
        'accessType': 'corporation'
    }

    messages = ['Upcoming Structure Maintenence Tasks']
    messages += check_citadels(esi_client, access_token, CORPORATION_ID)
    check_pos(xml_client, esi_client)

    params = {
        'text': '\n\n'.join(messages)
    }
    if SLACK_CHANNEL:
        params['channel'] = SLACK_CHANNEL
    results = requests.post(OUTBOUND_WEBHOOK, json=params)
    results.raise_for_status()
    print params

#!/usr/bin/env python

import os
import requests
import datetime
from bravado.client import SwaggerClient
from xml.etree.cElementTree import ElementTree as ET

SSO_APP_ID = os.getenv('SSO_APP_ID')
SSO_APP_KEY = os.getenv('SSO_APP_KEY')
SSO_REFRESH_TOKEN = os.getenv('SSO_REFRESH_TOKEN')
OUTBOUND_WEBHOOK = os.getenv('OUTBOUND_WEBHOOK')
TOO_SOON = int(os.getenv('TOO_SOON', 3))
CORPORATION_ID = int(os.getenv('CORPORATION_ID'))
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')


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


def check_citadels(esi_client, access_token, corporation_id):
    """
    Check citadels for fuel and services status
    """
    structures = esi_client.Corporation.get_corporations_corporation_id_structures(token=access_token, corporation_id=corporation_id).result()
    now = datetime.datetime.utcnow().date()
    too_soon = datetime.timedelta(days=TOO_SOON)
    messages = []
    for structure in structures:
        message = ''

        # Grab structure name
        structure_info = esi_client.Universe.get_universe_structures_structure_id(token=access_token, structure_id=structure['structure_id']).result()
        name = structure_info.get('name')

        # List online/offline services
        online_services = []
        offline_services = []
        for service in structure.get('services') or []:
            if service['state'] == 'online':
                online_services.append(service.get('name'))
            if service['state'] == 'offline':
                offline_services.append(service.get('name'))
        online = ', '.join([service for service in online_services])
        offline = ', '.join([service for service in offline_services])

        # Check when fuel expires
        fuel_expires = structure.get('fuel_expires', None)

        # Build message for fuel running out and offline services 
        if fuel_expires:
            how_soon = fuel_expires - now
            if how_soon < too_soon:
                message = "{} runs out of fuel on {}".format(name, fuel_expires)
                if online_services:
                    message += '\nOnline Services: {}'.format(online)
                if offline_services:
                    message += '\nOffline Services: {}'.format(offline)
        elif offline_services:
            message = '{} has offline services: {}'.format(name, offline)
        if message:
            messages.append(message)
    return messages

def xml_api(xml_client, endpoint, params=None):
    """
    Accesses CCP XML api in a useful way and returns ET root
    """
    xml_response = xml_client.get('https://api.eveonline.com' + endpoint, params=params)
    xml_root = et.fromstring(xml_response.content)
    try:
        xml_response.raise_for_status()
    except requests.HTTPError, e:
        xml_error = xml_root.find('.//error')
        message = "Error code {}: {}".format(xml_error.get('code'), xml_error.text)
        e.args = (message,)
        raise e
    return xml_root


def check_pos(xml_client, esi_client):
    pos_list_xml = xml_api(xml_client, '/corp/StarbaseList.xml.aspx')


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

    params = {
        'channel': SLACK_CHANNEL,
        'text': '\n\n'.join(messages)
    }
    requests.post(OUTBOUND_WEBHOOK, json=params)
    print params

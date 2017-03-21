#!/usr/bin/env python

import os
import requests
import datetime
from bravado.client import SwaggerClient

SSO_APP_ID = os.environ.get('SSO_APP_ID')
SSO_APP_KEY = os.environ.get('SSO_APP_KEY')
SSO_REFRESH_TOKEN = os.environ.get('SSO_REFRESH_TOKEN')
OUTBOUND_WEBHOOK = os.environ.get('OUTBOUND_WEBHOOK')

def get_access_token(refresh, client_id, client_secret):
	params = {
		'grant_type': 'refresh_token',
		'refresh_token': refresh
	}
	token_response = requests.post('https://login.eveonline.com/oauth/token', data=params, auth=(client_id, client_secret))
	token_response.raise_for_status()
	return token_response.json()['access_token']


client = SwaggerClient.from_url("https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility")

access_token = get_access_token(SSO_REFRESH_TOKEN, SSO_APP_ID, SSO_APP_KEY)

def check_citadels():
	structures = client.Corporation.get_corporations_corporation_id_structures(token=access_token, corporation_id=98444656).result()
	now = datetime.datetime.utcnow().date()
	too_soon = datetime.timedelta(days=5)
	messages = []
	for structure in structures:
		message = ''
		structure_info = client.Universe.get_universe_structures_structure_id(token=access_token, structure_id=structure['structure_id']).result()
		try:
			fuel_expires = structure['fuel_expires']
		except KeyError:
			fuel_expires = None
		name = structure_info['name']
		location_id = structure_info['solar_system_id']
		location_info = client.Universe.get_universe_systems_system_id(system_id=location_id).result()
		location_name = location_info['name']
		if fuel_expires:
			alert = ''
			how_soon = fuel_expires - now
			if how_soon < too_soon:
				alert = ' - THATS IN {} DAYS'.format(how_soon.days).upper()
				message = "{} in {} runs out of fuel on {}{}".format(name, location_name, fuel_expires, alert)
		if message:
			messages.append(message)
	return messages


if __name__ == '__main__':
	messages = []
	messages += check_citadels()
	print messages
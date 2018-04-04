#!/usr/bin/env python
#
# Freeze current ESI spec from https://esi.tech.ccp.is/_latest/swagger.json and format for useful diffs
#

import json
import requests
from bravado.client import SwaggerClient

response = requests.get('https://esi.tech.ccp.is/_latest/swagger.json')
response.raise_for_status()
SwaggerClient.from_spec(response.json(), config={'use_models': False})
with open('esi.json', 'w') as specfile:
	json.dump(response.json(), specfile, indent=4)


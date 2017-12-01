#!/usr/bin/env python
#
# Freeze current ESI spec from https://esi.tech.ccp.is/_latest/swagger.json and format for useful diffs
#

import json
import requests

response = requests.get('https://esi.tech.ccp.is/_latest/swagger.json')
response.raise_for_status()
with open('esi.json', 'w') as spec:
	json.dump(response.json(), spec, indent=4)

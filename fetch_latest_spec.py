#!/usr/bin/env python
#
# Freeze current ESI spec from https://esi.tech.ccp.is/_latest/swagger.json and format for useful diffs
#

import json
import requests
from swagger_spec_validator.common import SwaggerValidationError
from bravado.client import SwaggerClient
from bravado.swagger_model import load_file

response = requests.get('https://esi.tech.ccp.is/_latest/swagger.json')
response.raise_for_status()
SwaggerClient.from_spec(response.json())
with open('esi.json', 'w') as specfile:
	json.dump(response.json(), specfile, indent=4)


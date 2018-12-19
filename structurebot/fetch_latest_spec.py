#!/usr/bin/env python
#
# Freeze current ESI spec from https://esi.tech.ccp.is/_latest/swagger.json and format for useful diffs
#

import json
import requests
from esipy import App

app = App.create('https://esi.evetech.net/_latest/swagger.json', strict=True)

with open('esi.json', 'w') as specfile:
    json.dump(app.dump(), specfile, indent=4)


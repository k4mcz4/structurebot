#!/usr/bin/env python
#
# Convert SDE invControlTowerResources into python python dict

import sqlite3
import pprint

pprinter = pprint.PrettyPrinter()

conn = sqlite3.connect('sqlite-latest.sqlite')
c = conn.cursor()


pos_fuel = {}

pos_query = """select t.controlTowerTypeID, p.purposeText, t.resourceTypeID, i.typeName, t.quantity \
from invControlTowerResources as t \
join invControlTowerResourcePurposes as p on t.purpose = p.purpose \
join invTypes as i on t.resourceTypeID = i.typeID
"""

# invControlTowerResources
for row in conn.execute(pos_query):
	(controlTowerTypeID, purpose, resourceTypeID, resourceTypeName, quantity) = row
	tower_dict = pos_fuel.setdefault(controlTowerTypeID, {})
	tower_dict[resourceTypeID] = {'typeName': resourceTypeName, 'quantity': quantity}

moon_goo = {}

goo_query = 'select typeID, typeName, volume from invTypes where groupID = 427'

# invTypes
for row in conn.execute(goo_query):
	(typeID, typeName, volume) = row
	moon_goo[typeID] = {'typeName': typeName, 'volume': volume}

with open('pos_resources.py', 'w') as resources:
	resources.write('pos_fuel = ' + pprinter.pformat(pos_fuel))
	resources.write('\n\n')
	resources.write('moon_goo = ' + pprinter.pformat(moon_goo))

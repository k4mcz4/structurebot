#!/usr/bin/env python
#
# Convert SDE invControlTowerResources into python python dict

import sqlite3
import pprint

pprinter = pprint.PrettyPrinter()

conn = sqlite3.connect('sqlite-latest.sqlite')
c = conn.cursor()


pos_fuel = {}
fuel_types = {}

pos_query = """select t.controlTowerTypeID, p.purposeText, t.resourceTypeID, \
i.typeName, i.volume, t.quantity \
from invControlTowerResources as t \
join invControlTowerResourcePurposes as p on t.purpose = p.purpose \
join invTypes as i on t.resourceTypeID = i.typeID
"""

# invControlTowerResources
for row in conn.execute(pos_query):
    (controlTowerTypeID, purpose, resourceTypeID, resourceTypeName, volume, quantity) = row
    tower_dict = pos_fuel.setdefault(controlTowerTypeID, {})
    if resourceTypeID not in fuel_types:
        fuel_types[resourceTypeID] = {'typeName': resourceTypeName, 'volume': volume}
    tower_dict[resourceTypeID] = quantity

with open('pos_resources.py', 'w') as resources:
    resources.write('pos_fuel = ' + pprinter.pformat(pos_fuel))
    resources.write('\n\n')

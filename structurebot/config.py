from __future__ import absolute_import
import os
import datetime

CONFIG = {
    'NEUCORE_HOST': os.getenv('NEUCORE_HOST'),
    'NEUCORE_APP_ID': os.getenv('NEUCORE_APP_ID'),
    'NEUCORE_APP_SECRET': os.getenv('NEUCORE_APP_SECRET'),
    'NEUCORE_DATASOURCE': os.getenv('NEUCORE_DATASOURCE'),

    'OUTBOUND_WEBHOOK': os.getenv('OUTBOUND_WEBHOOK'),

    'ESI_HOST': os.getenv('ESI_HOST'),
    'CORPORATION_NAME': os.getenv('CORPORATION_NAME'),
    'TOO_SOON': datetime.timedelta(days=int(os.getenv('TOO_SOON', 3))),
    'STRONT_HOURS': int(os.getenv('STRONT_HOURS', 12)),
    'DETONATION_WARNING': datetime.timedelta(days=int(os.getenv('DETONATION_WARNING', 1))),
    'JUMPGATE_FUEL_WARN': int(os.getenv('JUMPGATE_FUEL_WARN', 500000)),
    'IGNORE_POS': os.getenv('IGNORE_POS', False),

    'DEBUG': os.getenv('DEBUG', False),
    'USER_AGENT': os.getenv('USER_AGENT', 'https://github.com/eve-n0rman/structurebot')
}

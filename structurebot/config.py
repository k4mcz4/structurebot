from __future__ import absolute_import
import os
import datetime

CONFIG = {
    'NEUCORE_HOST': os.getenv('NEUCORE_HOST', ''),
    'NEUCORE_APP_ID': os.getenv('NEUCORE_APP_ID', ''),
    'NEUCORE_APP_SECRET': os.getenv('NEUCORE_APP_SECRET', ''),
    'NEUCORE_APP_TOKEN': os.getenv('NEUCORE_APP_TOKEN', ''),
    'NEUCORE_DATASOURCE': os.getenv('NEUCORE_DATASOURCE', ''),
    'USER_AGENT': os.getenv('USER_AGENT', 'https://github.com/eve-n0rman/structurebot'),
    'ESI_CACHE': os.getenv('ESI_CACHE'),
    'OUTBOUND_WEBHOOK': os.getenv('OUTBOUND_WEBHOOK'),
    'TOO_SOON': datetime.timedelta(days=int(os.getenv('TOO_SOON', 3))),
    'CORPORATION_NAME': os.getenv('CORPORATION_NAME'),
    'IGNORE_POS': os.getenv('IGNORE_POS', False),
    'STRONT_HOURS': int(os.getenv('STRONT_HOURS', 12)),
    'DEBUG': os.getenv('DEBUG', False),
    'DETONATION_WARNING': datetime.timedelta(days=int(os.getenv('DETONATION_WARNING', 1))),
    'JUMPGATE_FUEL_WARN': int(os.getenv('JUMPGATE_FUEL_WARN', 500000))
}

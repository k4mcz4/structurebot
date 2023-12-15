from __future__ import absolute_import
import os
import datetime
import base64

CONFIG = {
    'NEUCORE_HOST': os.getenv('NEUCORE_HOST', 'https://neucore.tian-space.net/api/app/v2/esi'),
    'NEUCORE_APP_ID': os.getenv('NEUCORE_APP_ID', '21'),
    'NEUCORE_APP_SECRET': os.getenv('NEUCORE_APP_SECRET', '148906e7b33c6f5698b50d1f7e1cde9db6da6d20422cb635119c72b9c2957b6d'),
    'NEUCORE_APP_TOKEN': os.getenv('NEUCORE_APP_TOKEN', ''),
    'NEUCORE_DATASOURCE': os.getenv('NEUCORE_DATASOURCE', '91671644:temp-structurebot-1'),
    'USER_AGENT': os.getenv('USER_AGENT', 'https://github.com/eve-n0rman/structurebot'),
    'ESI_CACHE': os.getenv('ESI_CACHE'),
    'OUTBOUND_WEBHOOK': os.getenv('OUTBOUND_WEBHOOK'),
    'TOO_SOON': datetime.timedelta(days=int(os.getenv('TOO_SOON', 3))),
    'CORPORATION_NAME': os.getenv('CORPORATION_NAME','Solar Flare Exploration'),
    'IGNORE_POS': os.getenv('IGNORE_POS', False),
    'STRONT_HOURS': int(os.getenv('STRONT_HOURS', 12)),
    'DEBUG': os.getenv('DEBUG', False),
    'DETONATION_WARNING': datetime.timedelta(days=int(os.getenv('DETONATION_WARNING', 1))),
    'JUMPGATE_FUEL_WARN': int(os.getenv('JUMPGATE_FUEL_WARN', 500000))
}

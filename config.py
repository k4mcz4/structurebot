import os

SSO_APP_ID = os.getenv('SSO_APP_ID')
SSO_APP_KEY = os.getenv('SSO_APP_KEY')
SSO_REFRESH_TOKEN = os.getenv('SSO_REFRESH_TOKEN')
OUTBOUND_WEBHOOK = os.getenv('OUTBOUND_WEBHOOK')
TOO_SOON = int(os.getenv('TOO_SOON', 3))
CORPORATION_ID = int(os.getenv('CORPORATION_ID'))
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', None)
SOV_HOLDER = os.getenv('SOV_HOLDER', 'Brave Collective')
STRONT_HOURS = os.getenv('STRONT_HOURS', 12)

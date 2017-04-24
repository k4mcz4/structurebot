#!/usr/bin/env python

from config import *
from util import get_access_token, notify_slack, esi_client, xml_client
from citadels import check_citadels
from pos import check_pos


if __name__ == '__main__':


    access_token = get_access_token(SSO_REFRESH_TOKEN, SSO_APP_ID, SSO_APP_KEY)

    xml_client.params = {
        'accessToken': access_token,
        'accessType': 'corporation'
    }

    messages = ['Upcoming Structure Maintenence Tasks']
    messages += check_citadels(esi_client, access_token, CORPORATION_ID)
    messages += check_pos(xml_client, esi_client)
    notify_slack(messages)



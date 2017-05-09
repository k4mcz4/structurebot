#!/usr/bin/env python

from config import *
from util import get_access_token, notify_slack, xml_client
from citadels import check_citadels
from pos import check_pos


if __name__ == '__main__':


    access_token = get_access_token(SSO_REFRESH_TOKEN, SSO_APP_ID, SSO_APP_KEY)

    xml_client.params = {
        'accessToken': access_token,
        'accessType': 'corporation'
    }

    messages = []
    messages += check_citadels(access_token, CORPORATION_ID)
    messages += check_pos()
    if messages:
    	messages.insert(0, 'Upcoming Structure Maintenence Tasks')
    	notify_slack(messages)



#!/usr/bin/env python

from config import CONFIG
from util import notify_slack, name_to_id
from citadels import check_citadels
from pos import check_pos


if __name__ == '__main__':
    CONFIG['CORP_ID'] = name_to_id(CONFIG['CORPORATION_NAME'], 'corporation')
    messages = []
    try:
    	messages += check_citadels()
    	messages += check_pos()
    except Exception, e:
        if CONFIG['DEBUG']:
            raise
    	if e.message:
    		messages = [e.message]
    	else:
    		raise
    if messages:
    	messages.insert(0, ' Upcoming {} Structure Maintenence Tasks'.format(CONFIG['CORPORATION_NAME']))
    	notify_slack(sorted(messages))



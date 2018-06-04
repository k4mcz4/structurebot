#!/usr/bin/env python

from structurebot.config import CONFIG
from structurebot.util import notify_slack, name_to_id
from structurebot.citadels import check_citadels
from structurebot.assets import Asset
from structurebot.pos import check_pos


if __name__ == '__main__':
    corp_name = CONFIG['CORPORATION_NAME']
    CONFIG['CORP_ID'] = name_to_id(corp_name, 'corporation')
    assets = Asset.from_name(corp_name)
    messages = []
    try:
    	messages += check_citadels(corp_name, assets)
    	messages += check_pos(corp_name, assets)
    except Exception, e:
        if CONFIG['DEBUG']:
            raise
    	if e.message:
    		messages = [e.message]
    	else:
    		raise
    if messages:
    	messages.insert(0, ' Upcoming {} Structure Maintenence Tasks'.format(corp_name))
    	notify_slack(sorted(messages))



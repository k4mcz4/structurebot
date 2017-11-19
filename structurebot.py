#!/usr/bin/env python

from config import *
from util import notify_slack
from citadels import check_citadels
from pos import check_pos


if __name__ == '__main__':
    messages = []
    messages += check_citadels()
    messages += check_pos()
    if messages:
    	messages.insert(0, ' Upcoming {} Structure Maintenence Tasks'.format(CORPORATION_NAME))
    	notify_slack(sorted(messages))



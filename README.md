Develop: [![Build Status](https://travis-ci.org/eve-n0rman/structurebot.svg?branch=develop)](https://travis-ci.org/eve-n0rman/structurebot)
[![Coverage Status](https://coveralls.io/repos/github/eve-n0rman/structurebot/badge.svg?branch=develop)](https://coveralls.io/github/eve-n0rman/structurebot?branch=develop)

Master: [![Build Status](https://travis-ci.org/eve-n0rman/structurebot.svg?branch=master)](https://travis-ci.org/eve-n0rman/structurebot)
[![Coverage Status](https://coveralls.io/repos/github/eve-n0rman/structurebot/badge.svg?branch=master)](https://coveralls.io/github/eve-n0rman/structurebot?branch=master)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Click the button above to deploy to a new Heroku app.  You'll need to configured the 'scheduler' add-on after setup to run 'python structurebot.py' however frequently you'd like it to run.  I suggest daily.

# structurebot
## EVE Online Structure Checker

structurebot will check your EVE Online POS and Citadels for fuel, mining silos, offline services, reinforcement, etc and push a notification to Slack.

## Configuration

The following config items need to be defined in the environment

**EVE SSO Config**
* SSO_APP_ID
* SSO_APP_KEY

The app ID and key you get from an application you define [here](https://developers.eveonline.com/applications) with the following scopes: 

    esi-calendar.read_calendar_events.v1
    esi-universe.read_structures.v1
    esi-corporations.read_structures.v1
    esi-assets.read_corporation_assets.v1
    esi-corporations.read_starbases.v1
    esi-industry.read_corporation_mining.v1

* SSO_REFRESH_TOKEN

Currently, you need to manually track down a refresh token.  You can do this by walking through the [SSO login process](http://eveonline-third-party-documentation.readthedocs.io/en/latest/sso/authentication.html) with whatever tools you're comfortable with.  I find [Postman](https://www.getpostman.com/) works well for this.

**Slack Configuration**

* OUTBOUND_WEBHOOK

Your Slack administrator will need to create a [webhook](https://api.slack.com/incoming-webhooks) for you to use to send messages to slack

* SLACK_CHANNEL

The channel or person you'd like Slack messages to go to

**EVE Configuration**

* TOO_SOON

How many days in advance you'd like to receive fuel or silo warnings

* CORPORATION_NAME

The name of the corp which owns the structures

* STRONT_HOURS

The minimum number of hours worth of stront you'd like your POS to have

* DETONATION_WARNING

How many days in advance to notify about scheduled detonations

* JUMPGATE_FUEL_WARNING

The minimum amount of liquid ozone in Ansiblex before a notification

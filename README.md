[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)


# structurebot
## EVE Online Structure Checker

structurebot will check your EVE Online POS and Citadels for fuel, mining silos, offline services, reinforcement, etc and push a notification to Slack.

## Configuration

The following config items need to be defined in the environment

**EVE SSO Config**
* SSO_APP_ID
* SSO_APP_KEY

The app ID and key you get from an application you define [here](https://developers.eveonline.com/applications) with the following scopes: 

    * corporationAssetsRead
    * corporationStructuresRead
    * esi-calendar.read_calendar_events.v1
    * esi-universe.read_structures.v
    * esi-corporations.read_structures.v1

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

* CORPORATION_ID

The corporation ID of the corp which owns the structures

* SOV_HOLDER

The name of your alliance, for calculating fuel/stront bonuses in sov space

* STRONT_HOURS

The minimum number of hours worth of stront you'd like your POS to have

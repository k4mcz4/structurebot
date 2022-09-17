# structurebot

## EVE Online Structure Checker

structurebot will check your EVE Online POS and Citadels for fuel, mining silos, offline services, reinforcement, 
etc and push a notification to Slack.

## Configuration

The following config items need to be defined in the environment

**EVE SSO Config**

Set these if you do not use a Neucore app (see next section).

* SSO_APP_ID
* SSO_APP_KEY

The app ID and key you get from an application you define [here](https://developers.eveonline.com/applications) 
with the following scopes: 

    esi-calendar.read_calendar_events.v1
    esi-universe.read_structures.v1
    esi-corporations.read_structures.v1
    esi-assets.read_corporation_assets.v1
    esi-corporations.read_starbases.v1
    esi-industry.read_corporation_mining.v1

The character needs the following roles: Station_Manager, Director, Accountant

* SSO_REFRESH_TOKEN

Currently, you need to manually track down a refresh token. You can do this by walking through the 
[SSO login process](https://docs.esi.evetech.net/docs/sso/web_based_sso_flow.html) with whatever tools you're 
comfortable with. I find [Postman](https://www.getpostman.com/) works well for this.

* REDIS_TLS_URL, REDIS_URL

Necessary for refresh token rotation. If provided, the refresh token is stored in Redis. REDIS_TLS_URL is
checked first, then REDIS_URL.

**Neucore Config**

This is an alternative to EVE SSO from above. If you set both environment variables (SSO_* and NEUCORE_*), Neucore
will be used.

1. Configure Neucore with an EVE Login with the scopes and roles from above.
2. Add a Neucore app with the `app-esi` role and access to the EVE login from step 1.

Then add the following environment variables:

* NEUCORE_HOST

The Neucore domain, e.g. `account.bravecollective.com`.

* NEUCORE_APP_TOKEN

The base64 encoded "Id:Secret" of the app.
 
* NEUCORE_DATASOURCE

The datasource parameter for Neucore ESI requests, e.g. `96061222:structures` (character ID:Login name), see also 
https://account.bravecollective.com/api.html#/Application%20-%20ESI/esiV1.

**Slack Configuration**

* OUTBOUND_WEBHOOK

Your Slack administrator will need to create a [webhook](https://api.slack.com/incoming-webhooks) for you to use 
to send messages to slack

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

* JUMPGATE_FUEL_WARN

The minimum amount of liquid ozone in Ansiblex before a notification

## Run

Runs with Python 3.8 and 3.9

### Deploy on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Click the button above to deploy to a new Heroku app.  You'll need to configure the 'scheduler' add-on after setup
to run 'python structurebot.py' however frequently you'd like it to run.  I suggest daily.

### Dev Env

```sh
# Install Python versions if necessary
$ sudo add-apt-repository ppa:deadsnakes/ppa
$ sudo apt-get update
$ sudo apt-get install python3.8 python3.8-venv python3.9 python3.9-venv

# Init, for 3.8
$ python3.8 -m venv .venv8
$ source .venv8/bin/activate
$ pip install pipenv
$ pipenv install --dev
$ deactivate

# Run
$ source .venv8/bin/activate
$ source ./.env
$ pytest
$ python structurebot.py [-d]
$ python structure-audit.py [-d] [--csv]
$ deactivate
```

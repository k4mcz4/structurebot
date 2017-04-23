import datetime

from config import *


def check_citadels(esi_client, access_token, corporation_id):
    """
    Check citadels for fuel and services status
    """
    structures = esi_client.Corporation.get_corporations_corporation_id_structures(token=access_token, corporation_id=corporation_id).result()
    now = datetime.datetime.utcnow().date()
    too_soon = datetime.timedelta(days=TOO_SOON)
    messages = []
    for structure in structures:
        message = ''

        # Grab structure name
        structure_info = esi_client.Universe.get_universe_structures_structure_id(token=access_token, structure_id=structure['structure_id']).result()
        name = structure_info.get('name')

        # List online/offline services
        online_services = []
        offline_services = []
        for service in structure.get('services') or []:
            if service['state'] == 'online':
                online_services.append(service.get('name'))
            if service['state'] == 'offline':
                offline_services.append(service.get('name'))
        online = ', '.join([service for service in online_services])
        offline = ', '.join([service for service in offline_services])

        # Check when fuel expires
        fuel_expires = structure.get('fuel_expires', None)

        # Build message for fuel running out and offline services 
        if fuel_expires:
            how_soon = fuel_expires - now
            if how_soon < too_soon:
                message = "{} runs out of fuel on {}".format(name, fuel_expires)
                if online_services:
                    message += '\nOnline Services: {}'.format(online)
                if offline_services:
                    message += '\nOffline Services: {}'.format(offline)
        elif offline_services:
            message = '{} has offline services: {}'.format(name, offline)
        if message:
            messages.append(message)
    return messages

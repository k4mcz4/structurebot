import requests

import logging

nc_cache_get = {} 
esi_cache_get = {} 

def try_nc_cache_get(neucore_prefix:str, params:dict):
    key=tuple(params.items())
    if key in nc_cache_get.keys():
        return nc_cache_get[key]
    return None

def store_nc_cache_get(neucore_prefix:str, params:dict,resp):
    key=tuple(params.items())
    nc_cache_get[key]=resp


def try_esi_cache_get(esiurl:str,params:dict):
    key=(esiurl,tuple(params.items()))
    if key in esi_cache_get.keys():
        return esi_cache_get[key]
    return None

def store_esi_cache_get(esiurl:str,params:dict,resp):
    key=(esiurl,tuple(params.items()))
    esi_cache_get[key]=resp




class NCR:
    def __init__(self,app_id:str,app_secret:str,datasource:str,neucore_prefix:str,useragent:str=None,esi_prefix:str="https://esi.evetech.net/latest",cache_nc=True,cache_esi=True) -> None:
        self.app_id = str(app_id)
        self.app_secret = str(app_secret)
        self.neucore_prefix=neucore_prefix
        self.esi_prefix=esi_prefix
        self.datasource = str(datasource)
        self.useragent = useragent
        self.cache_nc=cache_nc
        self.cache_esi=cache_esi


        self.nc_session = requests.Session()
        self.esi_session  = requests.Session()
        self.nc_session.auth = (self.app_id,self.app_secret)
        if useragent:
            self.nc_session.headers.update('User-Agent',useragent)
            self.esi_session.headers.update('User-Agent',useragent)


        
    def nc_get(self,endpoint:str,page:int=None,query:dict={}):
        """routes an ESI-GET through Neucore

        used for protected data

        Args:
            endpoint (str): the desired ESI endpoint
            page (int, optional): returns only the specified page. If None concats all pages into the initial request. Defaults to None.

        Returns:
            requests.Response : the requests response
            data : the json decoded response content
        """

        #TODO add caching here
        #TODO add page-handling
        params = query.copy()
        params.update({"esi-path-query" : endpoint,
                 "datasource":self.datasource})
        if page:
            params['page']=page
        
        resp = try_nc_cache_get(self.neucore_prefix, params=params)
        if not resp:
            resp = self.nc_session.get(self.neucore_prefix, params=params)
            if resp.status_code == 200 and self.cache_nc:
                # cache resp
                store_nc_cache_get(self.neucore_prefix, params=params,resp=resp)
        data = resp.json()

        if page:
            # only requested this page
            return resp, data
        
        if 'X-Pages' in resp.headers.keys():
            page_max = int(resp.headers['X-Pages'])
            page = 1
            while page <= page_max:
                page = page+1
                page_resp, page_data = self.nc_get(endpoint=endpoint,page=page,query=query)

                if type(data) == dict and type(page_data) == dict:
                    # update dictionaries
                    data.update(page_data)
                elif type(data) == list and type(page_data) == list:
                    # update dictionaries
                    data.append(page_data)
                else:
                    # we should only have lists and dicts
                    #TODO Log this!
                    pass
        return resp , data
    
    def esi_get(self,endpoint:str,page=None,query:dict={}):
        """makes a GET request directly to the ESI

        Used for public data

        Args:
            endpoint (str): the desired ESI endpoint

        Returns:
            requests.Response : the requests response generated
        """
        #TODO add caching here
        #TODO add page-handling
        
        params=query.copy()
        if page:
            params['page'] = page

        
        resp = try_esi_cache_get(self.esi_prefix+endpoint,params=params)
        if not resp:
            resp = self.esi_session.get(self.esi_prefix+endpoint,params=params)
            if resp.status_code == 200 and self.cache_esi:
                store_esi_cache_get(self.esi_prefix+endpoint,params=params,resp=resp)

        data = resp.json()

        if page:
            # only requested this page
            return resp, data
        
        if 'X-Pages' in resp.headers.keys():
            page_max = int(resp.headers['X-Pages'])
            page = 1
            while page <= page_max:
                page = page+1
                page_resp, page_data = self.esi_get(endpoint=endpoint,page=page,query=query)

                if type(data) == dict and type(page_data) == dict:
                    # update dictionaries
                    data.update(page_data)
                elif type(data) == list and type(page_data) == list:
                    # update dictionaries
                    data.append(page_data)
                else:
                    # we should only have lists and dicts
                    #TODO Log this!
                    pass
        return resp , data

    def nc_post(self,endpoint:str,data,page=None,query:dict={}):
        """routes an ESI-POST through Neucore

        used for protected data

        Args:
            endpoint (str): the desired ESI endpoint

        Returns:
            requests.Response : the requests response generated
        """
        #TODO add caching here
        #TODO add page-handling
        params = query.copy()
        params = {"esi-path-query" : endpoint,
                 "datasource":self.datasource}
        if page:
            params['page']=page
        resp = self.nc_session.post(self.neucore_prefix,data=data,params=params)
        data = resp.json()

        if page:
            # only requested this page
            return resp, data
        
        if 'X-Pages' in resp.headers.keys():
            page_max = int(resp.headers['X-Pages'])
            page = 1
            while page <= page_max:
                page = page+1
                page_resp, page_data = self.nc_post(endpoint=endpoint,data=data,page=page,query=query)

                if type(data) == dict and type(page_data) == dict:
                    # update dictionaries
                    data.update(page_data)
                elif type(data) == list and type(page_data) == list:
                    # update dictionaries
                    data.append(page_data)
                else:
                    # we should only have lists and dicts
                    #TODO Log this!
                    pass
        return resp , data
    
    def esi_post(self,endpoint:str,data,page=None,query:dict={}):
        """makes a POST request directly to the ESI

        used for protected data

        Args:
            endpoint (str): the desired ESI endpoint

        Returns:
            requests.Response : the requests response generated
        """
        #TODO add caching here
        #TODO add page-handling
        params=query.copy()

        if page:
            params['page']=page

        resp = self.esi_session.post(self.esi_prefix+endpoint,data=data,params=params)
        data = resp.json()

        if page:
            # only requested this page
            return resp, data
        
        if 'X-Pages' in resp.headers.keys():
            page_max = int(resp.headers['X-Pages'])
            page = 1
            while page <= page_max:
                page = page+1
                page_resp, page_data = self.esi_post(endpoint=endpoint,data=data,page=page,query=query)

                if type(data) == dict and type(page_data) == dict:
                    # update dictionaries
                    data.update(page_data)
                elif type(data) == list and type(page_data) == list:
                    # update dictionaries
                    data.append(page_data)
                else:
                    # we should only have lists and dicts
                    #TODO Log this!
                    pass
        return resp , data

    def get_universe_structures_structure_id(self,structure_id):
        endpoint = "/universe/structures/{structure_id}/".format(structure_id=structure_id)
        response, data = self.nc_get(endpoint=endpoint)
        return response, data
    
    def get_corporations_corporation_id_structures(self,corporation_id):
        endpoint = "/corporations/{corporation_id}/structures/".format(corporation_id=corporation_id)
        response, data = self.nc_get(endpoint=endpoint)
        return response, data
    
    def get_corporation_corporation_id_mining_extractions(self,corporation_id):
        endpoint = "/corporation/{corporation_id}/mining/extractions/".format(corporation_id=corporation_id)
        response, data = self.nc_get(endpoint=endpoint)
        return response, data
    
    def get_corporations_corporation_id_starbases_starbase_id(self,corporation_id,starbase_id,system_id):
        #todo fix request
        endpoint = "/corporations/{corporation_id}/starbases/{starbase_id}/".format(corporation_id=corporation_id,starbase_id=starbase_id)
        response, data = self.nc_get(endpoint=endpoint,query={'system_id':system_id})
        return response, data
    
    def get_corporations_corporation_id_starbases(self,corporation_id):
        endpoint = "/corporations/{corporation_id}/starbases/".format(corporation_id=corporation_id)
        response, data = self.nc_get(endpoint=endpoint)
        return response, data
    
    def get_universe_systems_system_id(self,system_id):
        endpoint = "/universe/systems/{system_id}/".format(system_id=system_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data
    

    def get_universe_moons_moon_id(self,moon_id):
        endpoint = "/universe/moons/{moon_id}/".format(moon_id=moon_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data
    
    def post_corporations_corporation_id_assets_locations(self,corporation_id,asset_ids:list):
        endpoint = "/corporations/{corporation_id}/assets/locations/".format(corporation_id=corporation_id)
        response, data = self.nc_post(endpoint=endpoint,data=asset_ids)
        return response, data
    

    def get_sovereignty_map(self):
        endpoint = "/sovereignty/map/"
        response, data = self.esi_get(endpoint=endpoint)
        return response, data

    def get_corporations_corporation_id(self,corporation_id):
        endpoint = "/corporations/{corporation_id}/".format(corporation_id=corporation_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data
    
    def post_universe_ids(self,ids:list):
        endpoint  = "/universe/ids/"
        response, data = self.esi_post(endpoint=endpoint,data=ids)
        return response, data
    
    def post_universe_names(self,names:list):
        endpoint = "/universe/names/"
        response, data = self.esi_post(endpoint=endpoint,data=names)
        return response, data

    def get_universe_constellations_constellation_id(self, constellation_id):
        endpoint = "/universe/constellations/{constellation_id}/".format(constellation_id=constellation_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data
    
    def get_universe_regions_region_id(self,region_id):
        endpoint = "/universe/regions/{region_id}/".format(region_id=region_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data
    
    def get_universe_categories_category_id(self,category_id):
        endpoint = "/universe/categories/{category_id}/".format(category_id=category_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data
    
    def get_universe_groups_group_id(self,group_id):
        endpoint = "/universe/groups/{group_id}/".format(group_id=group_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data

    def get_universe_types_type_id(self,type_id):
        endpoint = "/universe/types/{type_id}/".format(type_id = type_id)
        response, data = self.esi_get(endpoint=endpoint)
        return response, data


    def get_characters_character_id_assets(self,character_id):
        endpoint = "/characters/{character_id}/assets/".format(character_id=character_id)
        response, data = self.nc_get(endpoint=endpoint)
        return response, data
    
    def get_corporations_corporation_id_assets(self,corporation_id):
        endpoint = "/corporations/{corporation_id}/assets/".format(corporation_id=corporation_id)
        response, data = self.nc_get(endpoint=endpoint)
        return response, data


if __name__ == "__main__":

    app_id = 21
    app_secret = "af02d4e61ed5421012c6a6a18b0e02b7db4a4354d786d2d095cf167fbb4b53e0"
    charID = 90645894 # Jack Deloran
    logging.basicConfig(level=logging.DEBUG)
    
    connection = NCR(app_id,app_secret,charID,neucore_prefix="https://neucore.tian-space.net/api/app/v2/esi/latest")
    r,d = connection.get_sovereignty_map()
    print(d)
    print(r.status_code)
    
    #resp = requests.get("https://neucore.tian-space.net"+"/app/v1/show")
    #
    # print(resp.status_code)
    #print(resp.content)
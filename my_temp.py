from structurebot.util import ncr,name_to_id,names_to_ids,ids_to_names

import logging
import json
import requests
import http.client as http_client

#http_client.HTTPConnection.debuglevel = 1

logging.basicConfig(level=logging.DEBUG)

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

data = {'names':['GE-8JV']}
j_data = json.dumps(data,ensure_ascii=False).encode('utf-8')
#print(data,j_data)

print(name_to_id('GE-8JV','solar_system'))




header= {'Accept':'application/json'}
data  = ["CCP Zoetrope"]
#print("Header: ",header)
#print("Data: ",data)
#print("JSON Data: ",json.dumps(data))
r = requests.post(url='https://esi.evetech.net/latest/universe/ids',headers=header,data=json.dumps(data))
print(r.status_code,r.json())
#print(r.request.headers,r.request.body,r.request.url)

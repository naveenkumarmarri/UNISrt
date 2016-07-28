#!/usr/bin/env python
import json
import subprocess

from runtime.models import Node, Exnode, Extent
from runtime.unisrt import UNISrt

rt = UNISrt(init_unis=False)

command = ["curl", "https://omd.crest.iu.edu/CREST/check_mk/webapi.py?action=get_all_hosts&_username=omduser&_secret=CSMHMXABTXDFYENRKAIH&effective_attributes=1"]

proc = subprocess.Popen(command, stdout=subprocess.PIPE)
output = proc.stdout.read()

variables = json.loads(output.decode("utf-8"))

for key, value in variables.items():
    if key == 'result':
        for prop in value.values():
            print("creating host %s" % prop['hostname'])
            print("creating ipport %s" % prop['attributes']['ipaddress'])
            
            hostdata = {
                "$schema": "http://unis.crest.iu.edu/schema/20160630/node",
                "name": prop['hostname']
            }
            n = Node(data = hostdata)
            rt.insert(n, sync = True)
            
            ipportdata = {
                "ipaddress": prop['attributes']['ipaddress'],
                "attach": {
                    "node": n.selfRef
                }
            }
            rt.insert(ipport(data = ipportdata), sync = False)
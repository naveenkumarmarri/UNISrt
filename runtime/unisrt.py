import threading
from time import time
from copy import deepcopy
from websocket import create_connection
from collections import defaultdict

import runtime.settings as settings
import runtime.models.runtime_objects as rto
from runtime.rest.unis_client import UnisClient
from runtime.utils import *

logger = settings.get_logger('unisrt')

resource_classes = {}
RT_OBJECT_MAP = {}
for key,value in settings.SCHEMAS.items():
    if key is "data":
        res = "{k}".format(k=key).lower()
    else:
        res = "{k}s".format(k=key).lower()
    RT_OBJECT_MAP[value] = res
    resource_classes[res] = getattr(rto, key)

class RTResource(list):
    def __init__(self, indexes):
        super(RTResource, self).__init__()
        assert(isinstance(indexes, list))
        self._indexes = indexes
        for ind in indexes:
            setattr(self, ind, defaultdict())

    def __str__(self):
        return super(RTResource, self).__str__()

    def filter(self, prop, val):
        return list(filter(lambda x: getattr(x, prop)==val, self))

class UNISrt(object):
    '''
    This is the class represents UNIS in local runtime environment (local to the apps).
    All UNIS models defined in the periscope/settings.py will be represented as
    a corresponding item of the 'resources' list in this class.
    At the initialization phase, UNISrt will create an cache of the UNIS db, (and
    will maintain it consistent in a best-effort manner).
    '''
    
    def __init__(self, init_unis=True):
        logger.info("starting UNIS Network Runtime Environment...")
        fconf = get_file_config(settings.CONFIGFILE)
        self.conf = deepcopy(settings.STANDALONE_DEFAULTS)
        merge_dicts(self.conf, fconf)
        
        self.unis_url = str(self.conf['properties']['configurations']['unis_url'])
        self.ms_url = str(self.conf['properties']['configurations']['ms_url'])
        self.time_origin = int(time())

        self._unis = UnisClient(self.unis_url)
        self._subunisclient = {}

        self._resources = self.conf['resources']
        
        self._def_indexes = ["id"]
        for resource in self._resources:
            setattr(self, resource, RTResource(self._def_indexes))

        if init_unis:
            # construct the hierarchical representation of the network
            for resource in self._resources:
                self.pullRuntime(self, self._unis, self._unis.get(resource), resource, False)

    def insert(self, resource, sync=False):
        resource.validate(auto_id=True)
        res_name = RT_OBJECT_MAP[resource._schema_uri]
        model = resource_classes[res_name]
        res = getattr(self, res_name)
        res.append(resource)
        if sync:
            return model(self._unis.post(res_name, resource.as_dict()))
        return resource
    
    def delete(self, resource, sync=False):
        pass

    def update(self, resource, sync=False):
        pass

    def pullRuntime(self, mainrt, currentclient, data, resource_name, localnew):
        '''
        this function should convert the input data into Python runtime objects
        '''
        model = resource_classes[resource_name]
        
        if data and isinstance(data, list):
            # sorting: in unisrt res dictionaries, a newer record of same index will be saved
            data.sort(key=lambda x: x.get('ts', 0), reverse=False)
            for v in data:
                res = getattr(self, resource_name)
                res.append(model(v))
                            
    def pushRuntime(self, resource_name):
        pass
    
    def subscribeRuntime(self, resource_name, currentclient):
        pass

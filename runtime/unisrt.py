import threading
from time import time
from copy import deepcopy
from graph_tool.all import Graph
from websocket import create_connection
from collections import defaultdict

import settings
from runtime.rest.unis_client import UNISInstance, REST_EP_MAP
from runtime.models import *
from runtime.utils import *

logger = settings.get_logger('unisrt')

# map name strings to class objects
resources_classes = {
    "domains": Domain,
    "nodes": Node,
    "ports": Port,
    "links": Link,
    "services": Service,
    "paths": Path,
    "measurements": Measurement,
    "metadata": Metadata,
    "exnodes": Exnode,
    "extents": Extent
}

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
        return filter(lambda x: getattr(x, prop)==val, self)

class UNISrt(object):
    '''
    This is the class represents UNIS in local runtime environment (local to the apps).
    All UNIS models defined in the periscope/settings.py will be represented as
    a corresponding item of the 'resources' list in this class.
    At the initialization phase, UNISrt will create an cache of the UNIS db, (and
    will maintain it consistent in a best-effort manner).
    '''
    
    def __init__(self):
        logger.info("starting UNIS Network Runtime Environment...")
        fconf = get_file_config(settings.CONFIGFILE)
        self.conf = deepcopy(settings.STANDALONE_DEFAULTS)
        merge_dicts(self.conf, fconf)
        
        self.unis_url = str(self.conf['properties']['configurations']['unis_url'])
        self.ms_url = str(self.conf['properties']['configurations']['ms_url'])
        self.time_origin = int(time())

        self._unis = UNISInstance(self.conf)
        self._subunisclient = {}

        self._resources = self.conf['resources']
        
        self._def_indexes = ["id"]
        for resource in self._resources:
            setattr(self, resource, RTResource(self._def_indexes))
        
        # construct the hierarchical representation of the network
        for resource in self._resources:
            # only pullRuntime once at the beginning, as pubsub will only update
            # them later when resources are modified on the server
            self.pullRuntime(self, self._unis, self._unis.get(resource), resource, False)
        
        # construct the graph representation of the network, of which this NRE is in charge
        self.g = Graph()
        self.nodebook = {}
        #for key in self.nodes['existing'].keys():
        #    self.nodebook[key] = self.g.add_vertex()
        #
        #for key, link in self.links['existing'].iteritems():
        #    if hasattr(link, 'src') and hasattr(link, 'dst'):
        #        self.g.add_edge(self.nodebook[link.src.node.selfRef],\
        #                        self.nodebook[link.dst.node.selfRef], add_missing=False)

    def insert(self, resource, sync=False):
        resource.validate()
        res_name = REST_EP_MAP[resource._schema_uri]
        res = getattr(self, res_name)
        res.append(resource)
        if sync:
            url = "{0}/{1}".format(self.unis_url, res_name)
            self._unis.post(url, resource.as_dict())
    
    def delete(self, resource, sync=False):
        pass

    def update(self, resource, sync=False):
        pass

    def pullRuntime(self, mainrt, currentclient, data, resource_name, localnew):
        '''
        this function should convert the input data into Python runtime objects
        '''
        model = resources_classes[resource_name]
        
        print resource_name
        if data and 'redirect' in data and 'instances' in data:
            if len(data['instances']) == 0:
                return
            
            for instance_url in data['instances']:
                if instance_url == 'https://dlt.crest.iu.edu:9000':
                    # TODO: needs SSL, not figured out yet, pretend it does not exist for now
                    continue
                
                if instance_url not in self._subunisclient:
                    conf_tmp = deepcopy(self.conf)
                    conf_tmp['properties']['configurations']['unis_url'] = instance_url
                    conf_tmp['properties']['configurations']['ms_url'] = instance_url # assume ms is the same as unis
                    self._subunisclient[instance_url] = unis_client.UNISInstance(conf_tmp)
                
                unis_tmp = self._subunisclient[instance_url]
                
                self.pullRuntime(mainrt, unis_tmp, unis_tmp.get(resource_name), resource_name, False)
                    
        elif data and isinstance(data, list):
            # sorting: in unisrt res dictionaries, a newer record of same index will be saved
            data.sort(key=lambda x: x.get('ts', 0), reverse=False)
            for v in data:
                res = getattr(self, resource_name)
                res.append(model(v))
                
            #threading.Thread(name=resource_name + '@' + currentclient.config['unis_url'],\
            #                 target=self.subscribeRuntime, args=(resource_name, self._unis,)).start()
            
    def pushRuntime(self, resource_name):
        '''
        this function upload specified resource to UNIS
        '''
        def pushEntry(k, entry):
            # TODO: use attribute "ts" to indicate an object downloaded from UNIS
            # for this sort of objects, only update their values.
            # this requires to remove "id" from all local created objects, not done yet
            if hasattr(entry, 'ts'):
                url = '/' + resource_name + '/' + getattr(entry, 'id')
                data = entry.prep_schema()

                self._unis.put(url, data)
#                the put() function may not do pubsub, so change to existing manually
#                if k in getattr(self, resource_name)['existing'] and isinstance(getattr(self, resource_name)['existing'][k], list):
#                    getattr(self, resource_name)['existing'][k].append(entry)
#                else:
#                    getattr(self, resource_name)['existing'][k] = entry
                
            else:
                url = '/' + resource_name
                data = entry.prep_schema()
                
                ret = self._unis.post(url, data)
                '''
                TODO: OSiRIS special
                groups = data['service'].split('/')
                tmp = '/'.join(groups[:3])
                su = self._subunisclient[tmp]
                ret = su.post(url, data)
                a = ret
                '''

        while True:
            try:
                key, value = getattr(self, resource_name)['new'].popitem()
                
                if not isinstance(value, list):
                    pushEntry(key, value)
                else:
                    for item in value:
                        pushEntry(key, item)
                    
            except KeyError:
                return
    
    def subscribeRuntime(self, resource_name, currentclient):
        '''
        subscribe a channel(resource) to UNIS, and listen for any new updates on that channel
        TODO: don't know how to subscribe in hierarchical unis. to whom it should subscribe?
        '''
        #name = resources_subscription[resource_name]
        name = resource_name
        model = resources_classes[resource_name]
        
        #url = self.unis_url.replace('http', 'ws', 1)
        unis_url = currentclient.config['unis_url']
        url = unis_url.replace('http', 'ws', 1)
        url = url + '/subscribe/' + name
        
        ws = create_connection(url)
        
        data = ws.recv()
        while data:
            model(json.loads(data), self, currentclient, False)
            data = ws.recv()
        ws.close()

    def poke_data(self, query):
        '''
        try to address this issue:
        - ms stores lots of data, and may be separated from unis
        - this data is accessible via /data url. They shouldn't be kept on runtime environment (too much)
        - however, sometimes they may be needed. e.g. HELM schedules traceroute measurement, and needs the
          results to schedule following iperf tests
        '''
        return self._unis.get('/data/' + query)
    
    def post_data(self, data):
        '''
        same as poke_data, the other way around
        '''
        #headers = self._def_headers("data")
        print data
        return self._unis.pc.do_req('post', '/data', data)#, headers)

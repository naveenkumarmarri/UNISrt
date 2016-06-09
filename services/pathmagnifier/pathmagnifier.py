import time
from copy import deepcopy

from kernel import models
from libnre.utils import *

TRACEROUTE = "ps:tools:blipp:linux:net:traceroute:hopip"

def getResourceLists(unisrt, ends, obj_class, obj_layer='l3'):
    '''
    INPUT:
    ends -- a pair of unis objects that can be the ends of a communication
    obj_layer -- specifies the interested layer of the returned resources
    obj_class -- specifies the interested object classes of the returned resources
                 needs to comply to obj_layer
    
    it takes a pair of unis objects (nodes, BLiPP services etc.), and return the resource list in between.
    it obtains the resources via various approaches:
    1. try to find the L3 hops directly from perfSONAR archive
    2. if failed, uses traceroute for BLiPP services* or forwarding simulation for nodes
    3. depends on the requested layers, L2 info may be queried by SSSP algorithm
    4. filter the right classes of objects
    
    ----------------------------------------------------
    * traceroute takes some time, therefore this function should be spawned concurrently to overlap the
      total waiting time, if there are multiple end pairs. shall address this ASAP.
    '''
    
    def incr(ntwkrsrc):
        '''
        currently, L2 graph is of name strings, rather than a graph of objects (should be updated momentarily)
        So, you need to know what object a name represent, in order to retrieve it from UNISrt
        '''
        if unisrt.unis_url + '/nodes/' + ntwkrsrc in unisrt.nodes['existing']:
            unisrt.nodes['existing'][unisrt.unis_url + '/nodes/' + ntwkrsrc].usecounter += 1
        elif ntwkrsrc in unisrt.links['existing']:
            unisrt.links['existing'][ntwkrsrc].usecounter += 1
            for s, d in unisrt.links['existing'][ntwkrsrc].endpoints.iteritems():
                try:
                    unisrt.ports['existing']['selfRef'][s].usecounter += 1
                    unisrt.ports['existing']['selfRef'][d].usecounter += 1
                except KeyError as e:
                    print e
        elif ntwkrsrc in unisrt.ipports['existing']:
            unisrt.ipports['existing'][ntwkrsrc].usecounter += 1
        else:
            print ntwkrsrc + " cannot be found in UNISrt"
    
    def vtraceroute(src, dst):
        '''
        use stored forwarding tables to figure the routes
        '''
        hops = [src]
        while hops[-1] != dst:
            out_port = hops[-1].services['routing'].rules[dst.id]
            the_link = unisrt.links['existing'][out_port]
            two_ends = the_link.endpoints
            the_other_end = two_ends.values()[0]
            the_node = unisrt.ports['existing'][the_other_end].node
            hops.append(the_link)
            hops.append(the_node)
        return hops
        
    def run_traceroute(src, dst):
        # start making a traceroute measurement object
        measurement = build_measurement(unisrt, src.selfRef)
        measurement['eventTypes'] = [TRACEROUTE]
        measurement['configuration']['name'] = "traceroute"
        measurement['configuration']['regex'] = "^\\s*\\d+.*(?P<hopip>\(.*\))"
        measurement['configuration']['eventTypes'] = {"hopip": TRACEROUTE}
        measurement['configuration']['probe_module'] = "traceroute_probe"        
        measurement['configuration']['collection_schedule'] = "builtins.simple"
        measurement['configuration']['reporting_params'] = 1
        measurement['configuration']['address'] = dst.ip
        measurement['configuration']['command'] = "traceroute %s" % measurement['configuration']['address']
                
        # some default fields, otherwise BLiPP will add this info itself and post the measurement again
        measurement['configuration']['collection_size'] = 10000000
        measurement['configuration']['collection_ttl'] = 1500000
        measurement['configuration']['schedule_params'] = {"every": 30}
        
        unisrt.updateRuntime([measurement], models.measurement, True)
        unisrt.uploadRuntime('measurements')
        
        while True:
            time.sleep(60)
            if '.'.join([measurement['selfRef'], TRACEROUTE]) in unisrt.metadata['existing']:
                # turn off this traceroute measurement, after it posted its result
                measurement['configuration']['status'] = "OFF"
                unisrt.updateRuntime([measurement], models.measurement, True)
                unisrt.uploadRuntime('measurements')
                
                hops = unisrt.poke_remote(unisrt.metadata['existing']['.'.join([measurement['selfRef'], TRACEROUTE])].id)
                return hops[0]['value']
        
    def psapi(src, dst):
        '''
        in case traceroute information can be found through periscope API (and downloaded as a file)
        '''
        try:
            with open('/home/mzhang/workspace/UNISrt/samples/HELM/i2_trace', 'r') as f:
                i2tr = json.load(f)
            with open('/home/mzhang/workspace/UNISrt/samples/HELM/esnet_trace', 'r') as f:
                esnettr = json.load(f)
                
            i2tr.update(esnettr)            
            return i2tr[' '.join([src, dst])]
        
        except (IOError, KeyError):
            return None

    
    # 1. query archive
    hops = psapi(ends[0].name, ends[-1].name)
    
    if not hops:
        if type(ends[0]) is models.service:
            # 2. assign traceroute tasks if BLiPP service instances
            hops = run_traceroute(ends[0], ends[-1])    
        elif type(ends[0]) is models.node:
            # 3. consult soft forwarding tables if just nodes
            hops = vtraceroute(ends[0], ends[-1])
        else:
            print "ERROR: run out of ideas resolving the hops"
            return None
    
    if obj_layer == 'l3':
        return filter(lambda x: type(x) is obj_class, hops)

    # from here to the end, attempt to expend l3 to multi-layer
    multi_hops = hops
    ip_resolver = unisrt.ipresolver # TODO: not done yet, but nre should have an ipport dict for ip-to-L2port query

    load = []
    temp = deepcopy(multi_hops)
    for hop in temp:
        if hop in ip_resolver:
            incr(hop)
            multi_hops[multi_hops.index(hop)] = ip_resolver[hop] # at the IP-L2 edge, we only map the vertex to a node(switch/router)
            load.append(ip_resolver[hop])
        else:
            # when an IP hop cannot be mapped to a L2 port, it's like floating in the air
            # it exists in the L3 topo but lacks info to tie it to any hardware.
            # these are the third kind of ipports (first two kinds are built by rspec and router config respectively)
            # don't upload ipport at this moment
            models.ipport({'address':{'address': hop, 'type': 'ipv4'}}, unisrt, False)
            incr(hop)
            del load[:]

        if len(load) == 2:
            resourcesL2 = []
            map(lambda x: resourcesL2.extend(list(x)), unisrt.graphL2.dijkstra(*load)[1])
            multi_hops[multi_hops.index(ip_resolver[hop]) - 1 : multi_hops.index(ip_resolver[hop]) + 1] = resourcesL2[:-1]
            load = [load[1]]
                    
    # update counters after the entire path got identified, to avoid double counting on an adjacent switch
    map(incr, list(set(multi_hops) - set(temp)))

    return multi_hops
    
def getGENIResourceLists(unisrt, pairs):
    '''
    in GENI, L3 resources are hidden by either stitching VLANs or local VMs. It requires a different way to identify the path
    After users reserve their slice, the (stitching) manifest can be uploaded to UNIS paths objects for this function to query
    '''        
    paths = {}
    for pair in pairs:
        key = (pair[0], pair[1])
        hops = map(lambda x: x, unisrt.paths['existing'][pair[0] + '%' + pair[1]].hops)
        
        # dst_ip_set = map(lambda x: x.address, unisrt.services['existing'][pair['to']].node.ipports.values())
        # candi0 = unisrt.ports['existing'][unisrt.unis_url + "/ports/" + hops[0].replace('+', '_')].ip
        # candi1 = unisrt.ports['existing'][unisrt.unis_url + "/ports/" + hops[-1].replace('+', '_')].ip
        # dst_ip = filter(lambda x: x in dst_ip_set, [candi0, candi1])
        # assert len(dst_ip) == 1
        # dst_ip = dst_ip[0]
        # paths[(pair['from'], dst_ip)] = hops
        
        hops.insert(0, pair[0])
        hops.append(pair[1])
        paths[key] = hops
        
    return paths

def run(unisrt, kwargs):
    forecaster = Forecaster(unisrt)
    setattr(unisrt, 'forecaster', forecaster)
    
if __name__ == '__main__':
    import kernel.unisrt
    unisrt = kernel.unisrt.UNISrt()
    forecaster = Forecaster(unisrt, 'args')
    setattr(unisrt, 'forecaster', forecaster)
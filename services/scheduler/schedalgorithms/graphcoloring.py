import sys
import networkx as nx
from collections import defaultdict
import bisect

def coloring(graph, order):
    max_color = 0
    V = len(graph.nodes())
    saturation = defaultdict(list)
    
    for n in order:
        # Select color for node
        color = 0
        for c in saturation[n]:
            if c == color:
                color += 1
            else:
                break
        graph.node[n]['color'] = color
        
        # Saturate neighbors
        for neighbor in graph.neighbors(n):
            bisect.insort(saturation[neighbor], color)
        
    return graph

def smallest_last_vertex_ordering(graph):
    degree_map = graph.degree()
    max_degree = max(degree_map)
    degree = 0

    # Check the previous bucket, then return the first element of the
    # first bucket containing elements
    def _nextNode(ls, c):
        print(ls, c)
        for i in range(c - 1, max_degree + 1):
            if ls[i]:
                return ls[i].pop(), i
    
    buckets = defaultdict(list)
    order = list(range(len(graph)))
    for n in graph.nodes():
        buckets[degree_map[n]].append(n)
        
    for i in range(len(graph) - 1, -1, -1):
        smallest, degree = _nextNode(buckets, degree)
        order[i] = smallest
        for neighbor in graph.neighbors(smallest):
            print(degree_map)
            if neighbor in buckets[degree_map[neighbor]]:
                buckets[degree_map[neighbor]].remove(neighbor)
                degree_map[neighbor] -= 1
                buckets[degree_map[neighbor]].append(neighbor)
        
    return order
        
def construct_graph(tasks):
    '''
    input: a dictionary whose keys are src-dst pairs (a.k.a measurement events), values are required resource
    output: the intersection graph
    '''
    ug = nx.Graph()
    for i, p in enumerate(tasks.keys()):
        properties = {
            "measurement": p,
            "path": tasks[p],
            "marked": len(tasks),
            "color": -1
        }
        ug.add_node(i, **properties)
        for j, q in enumerate(list(tasks.keys())[i + 1 :], start = i + 1):
            if set(tasks[p]) & set(tasks[q]):
                ug.add_edge(i, j)
                
    return ug

def main():
    # We start with an empty, undirected graph
    ug = nx.Graph(directed = False)
    
    vlist = list(ug.add_node(12))
    
    ug.add_edge(vlist[0], vlist[1])
    ug.add_edge(vlist[1], vlist[2])
    ug.add_edge(vlist[2], vlist[3])
    ug.add_edge(vlist[2], vlist[4])
    ug.add_edge(vlist[3], vlist[6])
    ug.add_edge(vlist[3], vlist[7])
    ug.add_edge(vlist[3], vlist[8])
    ug.add_edge(vlist[4], vlist[5])
    ug.add_edge(vlist[4], vlist[9])
    ug.add_edge(vlist[4], vlist[10])
    ug.add_edge(vlist[4], vlist[11])
    ug.add_edge(vlist[6], vlist[7])
    ug.add_edge(vlist[6], vlist[8])
    ug.add_edge(vlist[6], vlist[9])
    ug.add_edge(vlist[6], vlist[10])
    ug.add_edge(vlist[6], vlist[11])
    
    vprop_order = [None] * ug.num_vertices()
    vprop_degree = ug.degree_property_map('total')
    bucketSorter = [[] for _ in range(ug.num_vertices())]
    smallest_last_vertex_ordering(ug, vprop_order, vprop_degree, bucketSorter)
    
    vprop_color = ug.new_vertex_property('int')
    coloring(ug, vprop_order, vprop_color)
    
    from graph_tool.draw import graph_draw
    graph_draw(ug)

    return

if __name__ == '__main__':
    main()

import sys
import networkx as nx

def coloring(graph, vprop_order, vprop_color):
    max_color = 0
    V = len(graph.nodes())
    mark = {}
    
    for v in graph.nodes():
        vprop_color[v] = V - 1 # which means "not colored"
        
    for i in range(V):
        current = vprop_order[i]
        
        # mark all the colors of the adjacent vertices
        for neighbour in nx.all_neighbors(graph, current):
            mark[vprop_color[neighbour]] = i
            
        # find the smallest color unused by the adjacent vertices
        smallest_color = 0
        while smallest_color < max_color and mark[smallest_color] == i:
            smallest_color += 1

        # if all the colors are used up, increase the number of colors
        if smallest_color == max_color:
            max_color += 1

        vprop_color[current] = smallest_color
        
    return max_color

def smallest_last_vertex_ordering(graph, vprop_order, vprop_degree, degree_buckets):
    num = len(graph.node)

    for v in graph.nodes():
        graph.node[v]["marked"] = num
        degree = vprop_degree[v]
        degree_buckets[degree].append(v)

    minimum_degree = 0
    current_order = num - 1

    while True:
        minimum_degree_stack = degree_buckets[minimum_degree]
        while not minimum_degree_stack:
            minimum_degree += 1
            minimum_degree_stack = degree_buckets[minimum_degree]
            
        node = minimum_degree_stack.pop()
        vprop_order[current_order] = node
        
        if current_order == 0:
            break

        vprop_marker[node] = 0
        
        for neighbour in node.all_neighbours():
            if vprop_marker[neighbour] > current_order:
                vprop_marker[neighbour] = current_order

                # delete v from the bucket sorter
                degree_buckets[vprop_degree[neighbour]].remove(neighbour)

                # it is possible minimum degree goes down, so we keep tracking it.
                # but, it is not 100% "smallest last"
                vprop_degree[neighbour] = vprop_degree[neighbour] - 1
                minimum_degree = min(minimum_degree, vprop_degree[neighbour])

                # re-insert v in the bucket sorter with the new degree
                degree_buckets[vprop_degree[neighbour]].append(neighbour)
            
        current_order -= 1
        
def construct_graph(tasks):
    '''
    input: a dictionary whose keys are src-dst pairs (a.k.a measurement events), values are required resource
    output: the intersection graph
    '''
    ug = nx.Graph()
    vprop_name = {}
    for i, p in enumerate(tasks.keys()):        
        ug.add_node(i, name=p, uid=i, marked=0)
        vprop_name[i] = p
        for j, q in enumerate(list(tasks.keys())[i + 1 :], start = i + 1):
            if set(tasks[p]) & set(tasks[q]):
                ug.add_edge(i, j)

    return ug, vprop_name

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

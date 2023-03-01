import requests
import json
import networkx as nx
import matplotlib.pyplot as plt

# retrieve list of switches
r = requests.get('http://localhost:8080/stats/switches', headers={'Cache-Control': 'no-cache'})
r = r.text
switches = json.loads(r)
n_switch = len(switches)
#set up links between switches

# Create a new empty graph
G = nx.Graph()

#add switches
for i in range(1, n_switch + 1):
    G.add_node("s" + str(i), color='yellow', group="switch")

# http://localhost:8080/v1.0/topology/links
r = requests.get('http://localhost:8080/v1.0/topology/links', headers={'Cache-Control': 'no-cache'})
r = r.text
s_links = json.loads(r)

#add switch to switch links
edges = []
for l in s_links:
    src = "s" + str(int(l["src"]['dpid'])) #doubl conversion bc id comes in the form 00000000000x
    dst = "s" + str(int(l["dst"]['dpid']))
    if (src,dst) not in edges and (dst,src) not in edges and src != dst:
        edges.append((src,dst))

# http://localhost:8080/v1.0/topology/hosts
r = requests.get('http://localhost:8080/v1.0/topology/hosts', headers={'Cache-Control': 'no-cache'})
r = r.text
h_links = json.loads(r)

#add hosts and host-switch links
for h in h_links:
    cur_host = int(h["mac"][-1]) + n_switch
    src = "h" + str(cur_host)
    dst = "s" + str(int(h["port"]["dpid"])) #doubl conversion bc id comes in the form 00000000000x

    G.add_node(src, color='green', group='host')
    if (src,dst) not in edges and (dst,src) not in edges and src != dst:
        edges.append((src,dst))
G.add_edges_from(edges)

node_colors = [G.nodes[n]['color'] for n in G.nodes]

# Draw the graph
nx.draw(G, node_color=node_colors, with_labels=True)

# Show the graph
plt.show()

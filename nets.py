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

# http://localhost:8080/v1.0/topology/links
r = requests.get('http://localhost:8080/v1.0/topology/links', headers={'Cache-Control': 'no-cache'})
r = r.text
s_links = json.loads(r)

edges = []
for l in s_links:
    src = int(l["src"]['dpid'])
    dst = int(l["dst"]['dpid'])
    if (src,dst) not in edges and (dst,src) not in edges and src != dst:
        edges.append((src,dst))

# http://localhost:8080/v1.0/topology/hosts
r = requests.get('http://localhost:8080/v1.0/topology/hosts', headers={'Cache-Control': 'no-cache'})
r = r.text
h_links = json.loads(r)

hosts = []
for h in h_links:
    cur_host = int(h["mac"][-1]) + n_switch
    hosts.append(cur_host)
    edges.append((cur_host, int(h["port"]["dpid"])))

print(switches)
print(hosts)
print(edges)


#retrieve list of hosts

#setup links between hosts and switches


# Create a new empty graph
G = nx.Graph()

# Add nodes
G.add_nodes_from(switches)

# Add edges
G.add_edges_from(edges)

# Draw the graph
nx.draw(G, with_labels=True)

# Show the graph
plt.show()

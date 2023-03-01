import json
import requests
import networkx as nx
import matplotlib.pyplot as plt

def on_node_click(event):
    label = event.artist.get_label()
    # print(f"You clicked host {node}")
    
    if is_node(label):
        node = label
        if G.nodes[node]['group'] == 'switch':
            print("ugugguu")
        elif  G.nodes[node]['group'] == 'host':
            print("auauauauau")
    else:
        print(label)


def is_node(label) -> bool:
    label = str(label)
    if label[0] == 's' or label[0] == 'h':
        return True
    else:
        return False

def on_edge_click(event):
    print("ciaiaosida")

# retrieve list of switches
r = requests.get('http://localhost:8080/stats/switches', headers={'Cache-Control': 'no-cache'})
r = r.text
switches = json.loads(r)
n_switch = len(switches)
#set up links between switches

# Create a new empty graph
G = nx.Graph()
fig, ax = plt.subplots()

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

pos=nx.spring_layout(G) #position of the elements in the figure, generate here, only once, to have everything aligned

for node in G.nodes():
    node_artist = nx.draw_networkx_nodes(G, pos=pos, nodelist=[node], node_color=G.nodes[node]['color'], node_size=500, ax=ax)
    node_artist.set_label(node)
    node_artist.set_picker(True)
    
for edge in G.edges():
    edge_art = nx.draw_networkx_edges(G, edgelist=[edge], pos=pos, ax=ax)
    edge_art.set_label(edge)
    edge_art.set_picker(True)

fig.canvas.mpl_connect('pick_event', on_node_click)
# nx.draw_networkx_edges(G, edgelist=G.edges(), pos=pos, ax=ax)

# Show the graph
plt.show()

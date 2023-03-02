import json
import requests
import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import numpy as np

import networkx as nx


class netsGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Network Visualizer")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        self.textbox = tk.Text(self.root, height=3)
        self.textbox.insert(tk.END, "ciaone start text")
        self.textbox.pack()


        self.btn = tk.Button(self.root, text="show msg", command=self.show_msg)
        self.btn.pack()

        exit_button = tk.Button(self.root, text="Exit", command=self._quit)
        exit_button.pack()

        self.graphbtn = tk.Button(self.root, text="Draw topology", command=self.drawgraph)
        self.graphbtn.pack()

        self.G = nx.Graph()
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        # self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.root.mainloop()

    def show_msg(self):
        # print(self.check_state.get())
        tmp = self.textbox.get("1.0", tk.END)
        self.textbox.delete("1.0",tk.END)
        self.textbox.insert(tk.END, tmp[int(len(tmp)/2):len(tmp)])

    def _quit(self):
        self.root.quit()
        self.root.destroy() 

    def drawgraph(self):
        # delete existing widget (it was easier than clearing the previous widget and redrawing the graph)
        try: 
            self.canvas.get_tk_widget().pack_forget()
        except AttributeError: 
            pass 

        self.G.clear()
        self.fig, self.ax = plt.subplots() #new figure for the new widget

        # retrieve list of switches
        r = requests.get('http://localhost:8080/stats/switches', headers={'Cache-Control': 'no-cache'})
        r = r.text
        switches = json.loads(r)
        n_switch = len(switches)

        for i in range(1, n_switch + 1):
            self.G.add_node("s" + str(i), color='yellow', group="switch")

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
            dst = "s" + str(int(h["port"]["dpid"])) #double conversion bc id comes in the form 00000000000x

            self.G.add_node(src, color='green', group='host')
            if (src,dst) not in edges and (dst,src) not in edges and src != dst:
                edges.append((src,dst))
        self.G.add_edges_from(edges)

        pos=nx.spring_layout(self.G) #position of the elements in the figure, generate here, only once, to have everything aligned

        for node in self.G.nodes():
            node_artist = nx.draw_networkx_nodes(self.G, pos=pos, nodelist=[node], node_color=self.G.nodes[node]['color'], node_size=500, ax=self.ax)
            node_artist.set_label(node)
            node_artist.set_picker(True)
            
        for edge in self.G.edges():
            edge_art = nx.draw_networkx_edges(self.G, edgelist=[edge], pos=pos, ax=self.ax)
            edge_art.set_label(edge)
            edge_art.set_picker(True)

        self.fig.canvas.mpl_connect('pick_event', self.on_node_click)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        # self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.graphbtn.config(text='Update topology')

    def on_node_click(self, event):
        label = event.artist.get_label()
        # print(f"You clicked host {node}")
        
        if self.is_node(label):
            node = label
            if self.G.nodes[node]['group'] == 'switch':
                print("ugugguu")
            elif self.G.nodes[node]['group'] == 'host':
                print("auauauauau")
        else:
            print(label)


    def is_node(self, label) -> bool:
        label = str(label)
        if label[0] == 's' or label[0] == 'h':
            return True
        else:
            return False

    def on_edge_click(self, event):
        print("ciaiaosida")


netsGUI()
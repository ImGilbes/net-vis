import os
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

SWITCH_COLOR = '#fee08b'
HOST_COLOR = "#66bd63"

FONT = ("Lucida Grande",18)

class netsGUI:
    def __init__(self):
        self.root = tk.Tk()

        self.root.title("Network Visualizer")
        self.root.geometry("900x900")
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        self.windowframe =tk.Frame(self.root, padx=120)
        self.windowframe.rowconfigure(0, weight=1)
        self.windowframe.rowconfigure(1, weight=1)
        self.windowframe.rowconfigure(2, weight=1)
        self.windowframe.rowconfigure(3, weight=1)

        self.textbox = tk.Text(self.windowframe)
        self.textbox.insert(tk.END, "")
        self.textbox.configure(state='disabled')
        # self.textbox.pack()
        self.textbox.grid(row=0,column=0,sticky=tk.W+tk.E)

        self.buttonframe = tk.Frame(self.windowframe)
        self.buttonframe.columnconfigure(0, weight=1)
        self.buttonframe.columnconfigure(1, weight=1)
        self.buttonframe.columnconfigure(2, weight=1)
        # self.buttonframe.pack(expand=True)

        self.btn = tk.Button(self.buttonframe, text="show msg", command=self.show_msg)
        # self.btn.pack()
        self.btn.grid(row=0,column=0,sticky=tk.W+tk.E)


        self.exit_button = tk.Button(self.buttonframe, text="Exit", command=self._quit)
        # exit_button.pack()
        self.exit_button.grid(row=2,column=2,sticky=tk.W+tk.E)

        self.graphbtn = tk.Button(self.buttonframe, text="Draw topology", command=self.drawgraph)
        # self.graphbtn.pack()
        self.graphbtn.grid(row=0,column=1,sticky=tk.W+tk.E)


        self.addflowbtn = tk.Button(self.buttonframe, text="New Flow", command=self.addflow)
        # self.graphbtn.pack()
        self.addflowbtn.grid(row=0,column=2,sticky=tk.W+tk.E)

        self.addqosbtn = tk.Button(self.buttonframe, text="New Qos", command=self.addqos)
        # self.graphbtn.pack()
        self.addqosbtn.grid(row=1,column=0,sticky=tk.W+tk.E)

        # self.addqosbtn.bind("<Button>",lambda e: tk.Toplevel(self.root))

        # self.buttonframe.pack(expand=True)
        self.buttonframe.grid(row=1,column=0,sticky=tk.W+tk.E)

        self.cmdbtn = tk.Button(self.windowframe, text="Execute", command=self.exec_cmd_txt)
        self.cmdtext = tk.Text(self.windowframe, height=6)
        self.cmdtext.grid(row=2,column=0,sticky=tk.W+tk.E)
        self.cmdbtn.grid(row=3,column=0)

        
        self.windowframe.pack(expand=True,fill='x')

        # topology display
        self.G = nx.Graph() # this will be cleared everytime you update topology
        self.fig, self.ax = plt.subplots() # these will be discarded and recreated
        self.ax.tick_params(top=False,
               bottom=False,
               left=False,
               right=False,
               labelleft=False,
               labelbottom=False)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root) #discarded and recreated
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True) #unpacked

        
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
        r = requests.get('http://localhost:8080/stats/switches', headers={'Cache-Control': 'no-cache, no-store'})
        r = r.text
        switches = json.loads(r)
        n_switch = len(switches)

        for i in range(1, n_switch + 1):
            self.G.add_node("s" + str(i), color=SWITCH_COLOR, group="switch")

        # http://localhost:8080/v1.0/topology/links
        r = requests.get('http://localhost:8080/v1.0/topology/links', headers={'Cache-Control': 'no-cache, no-store'})
        r = r.text
        s_links = json.loads(r)

        #add switch to switch links
        edges = []
        for l in s_links:
            src = "s" + str(int(l["src"]['dpid'], base=16)) #double conversion bc id comes in the form 00000000000x
            dst = "s" + str(int(l["dst"]['dpid'], base=16))
            if (src,dst) not in edges and (dst,src) not in edges and src != dst:
                edges.append((src,dst))

        # http://localhost:8080/v1.0/topology/hosts
        r = requests.get('http://localhost:8080/v1.0/topology/hosts', headers={'Cache-Control': 'no-cache, no-store'})
        r = r.text
        h_links = json.loads(r)

        #add hosts and host-switch links
        for h in h_links:
            # cur_host = int(h["mac"][-1], base=16) + n_switch #alternative name for hosts
            cur_host = int(h["mac"][-1], base=16)
            src = "h" + str(cur_host)
            dst = "s" + str(int(h["port"]["dpid"], base=16)) #double conversion bc id comes in the form 00000000000x

            self.G.add_node(src, color=HOST_COLOR, group='host')
            if (src,dst) not in edges and (dst,src) not in edges and src != dst:
                edges.append((src,dst))
        self.G.add_edges_from(edges)

        pos=nx.spring_layout(self.G) #position of the elements in the figure, generate here, only once, to have everything aligned

        for node in self.G.nodes():
            node_artist = nx.draw_networkx_nodes(self.G, pos=pos, nodelist=[node], node_color=self.G.nodes[node]['color'], node_size=600, ax=self.ax)
            node_artist.set_label(node)
            node_artist.set_picker(True)
        nx.draw_networkx_labels(self.G, pos=pos)
            
        for edge in self.G.edges():
            edge_art = nx.draw_networkx_edges(self.G, edgelist=[edge], pos=pos, ax=self.ax)
            edge_art.set_label(edge)
            edge_art.set_picker(True)

# hosts and switches are differentiated with networkx attributes -> G.nodes[<node_id>][<attr>] -> G.nodes[<node_id>]['group']

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
                self.on_switch_click(event)
            elif self.G.nodes[node]['group'] == 'host':
                self.on_host_click(event)
        else:
            self.on_edge_click(event)


    def is_node(self, label) -> bool:
        label = str(label)
        if label[0] == 's' or label[0] == 'h':
            return True
        else:
            return False
        
    def on_switch_click(self, event):
        label = event.artist.get_label()
        label = str(label)
        self.textbox.configure(state='normal')
        self.textbox.delete('1.0', tk.END)

        dpid = label[1:]
        # now prints the flow table
        r = requests.get(f'http://localhost:8080/stats/flow/{dpid}', headers={'Cache-Control': 'no-cache, no-store'})
        r = r.text
        flow = json.loads(r)
        flow = self.output_format_flowtable(flow)
        
        self.textbox.insert('1.0', f"Flow Table:{flow}")
        self.textbox.insert('1.0', f"Switch {label}\n")
        self.textbox.configure(state='disabled')

    def output_format_flowtable(self, flow) -> str:
        # print(flow['1'])
        ret = ""
        i = 1
        for tab in flow:
            # print(flow)
            for entry in flow[tab]:
                if 'match' in entry:
                    ret = ret + f"\n\n Entry {i}"
                    if 'dl_dst' in entry['match']:
                        ret = ret + f"\n - Destination address: {entry['match']['dl_dst']}"
                        if('dl_src' in entry['match']):
                            ret = ret + f"\n - Source address: {entry['match']['dl_src']}"
                        else:
                            ret = ret + " - No source specified"
                    if "in_port" in entry['match']:
                        ret = ret + f"\n - Input Port: {entry['match']['in_port']}"
                else:
                    ret = ret + " - No matches available for this entry"

                if 'actions' in entry:
                    ret = ret + f"\n - Actions: {entry['actions']}"
                else:
                    ret = ret + " - No actions available for this entry"
                
                if 'packet_count' in entry:
                    ret = ret + f"\n - Number of packets macthed : {entry['packet_count']}"
                
                i = i+1


                # self.textbox.insert('1.0', f"ENTRY\n{str(entry)}\n")
        return ret


    def on_host_click(self, event):
        label = event.artist.get_label()
        self.textbox.configure(state='normal')
        self.textbox.delete('1.0', tk.END)
        self.textbox.insert('1.0', f"Host {label}")
        self.textbox.configure(state='disabled')

    def on_edge_click(self, event):
        label = event.artist.get_label()
        self.textbox.configure(state='normal')
        self.textbox.delete('1.0', tk.END)
        self.textbox.insert('1.0', f"Edge {label}")
        self.textbox.configure(state='disabled')

    def exec_cmd_txt(self):
        cmd = self.cmdtext.get('1.0', tk.END)
        os.system(cmd)
        self.cmdtext.delete('1.0', tk.END)

    def addqos(self):
        pass

    def addflow(self):
        
        newwind = tk.Toplevel(self.root)
        newwind.geometry("400x400")
        windowframe =tk.Frame(newwind)
        windowframe.rowconfigure(0, weight=1)
        windowframe.rowconfigure(1, weight=1)
        windowframe.rowconfigure(2, weight=1)
        windowframe.rowconfigure(3, weight=1)
        windowframe.rowconfigure(4, weight=1)
        windowframe.columnconfigure(0, weight=1)
        windowframe.columnconfigure(1, weight=1)

        tk.Label(windowframe, text="Source NW Address").grid(row=0, column=0,sticky=tk.W+tk.E)
        tk.Label(windowframe, text="Destination NW Address").grid(row=1, column=0,sticky=tk.W+tk.E)
        tk.Label(windowframe, text="Action").grid(row=2, column=0,sticky=tk.W+tk.E)
        tk.Label(windowframe, text="Priority").grid(row=3, column=0,sticky=tk.W+tk.E)
        tk.Label(windowframe, text="IdleTimeout").grid(row=4, column=0,sticky=tk.W+tk.E)

        e1 = tk.Entry(windowframe)
        e2 = tk.Entry(windowframe)
        e3 = tk.Entry(windowframe)
        e4 = tk.Entry(windowframe)
        e5 = tk.Entry(windowframe)

        e1.grid(row=0, column=1,sticky=tk.W)
        e2.grid(row=1, column=1,sticky=tk.W)
        e3.grid(row=2, column=1,sticky=tk.W)
        e4.grid(row=3, column=1,sticky=tk.W)
        e5.grid(row=4, column=1,sticky=tk.W)

        btnframe =tk.Frame(newwind)
        windowframe.columnconfigure(0, weight=1)

        def newflow_creation():

            print("Ciao")
            print(f"{e1.get()}")

        createbtn = tk.Button(btnframe, text="Add Flow", command=newflow_creation)
        createbtn.grid(row=0,column=0,sticky=tk.E+tk.W+tk.N)

        windowframe.pack(expand=True,fill='both')
        btnframe.pack(expand=True,fill='x', padx=40)

        
        
        #         tk.Label(master, 
        #         text="First Name").grid(row=0)
        # tk.Label(master, 
        #         text="Last Name").grid(row=1)

        # e1 = tk.Entry(master)
        # e2 = tk.Entry(master)

        # e1.grid(row=0, column=1)
        # e2.grid(row=1, column=1)

        # tk.Button(master, 
        #         text='Quit', 
        #         command=master.quit).grid(row=3, 
        #                                     column=0, 
        #                                     sticky=tk.W, 
        #                                     pady=4)
        # tk.Button(master, 
        #         text='Show', command=show_entry_fields).grid(row=3, 
        #                                                     column=1, 
        #                                                     sticky=tk.W, 
        #                                                     pady=4)




netsGUI()
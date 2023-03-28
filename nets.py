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
from tkinter import font

SWITCH_COLOR = '#fee08b'
HOST_COLOR = "#66bd63"

def_font=('Helvetica', 11)

DEFAULT_IDLE = "0"
DEFAULT_HARD = "0"
DEFAULT_PRIORITY = "11111"

class netsGUI:
    def __init__(self):
        self.root = tk.Tk()

        self.root.title("Network Visualizer")
        self.root.geometry("900x900")
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        #https://stackoverflow.com/questions/47769187/make-anacondas-tkinter-aware-of-system-fonts-or-install-new-fonts-for-anaconda
        #https://github.com/ContinuumIO/anaconda-issues/issues/6833
        #basically it says i cannot change the fonts
        #i've just settled for fontsize :(
        
        
        self.windowframe =tk.Frame(self.root, padx=100)
        self.windowframe.rowconfigure(0, weight=1)
        self.windowframe.rowconfigure(1, weight=1)
        self.windowframe.rowconfigure(2, weight=1)
        self.windowframe.rowconfigure(3, weight=1)
        

        self.textbox = tk.Text(self.windowframe, font=def_font)
        self.textbox.insert(tk.END, "")
        self.textbox.configure(state='disabled')
        # self.textbox.pack()
        self.textbox.grid(row=0,column=0,sticky=tk.W+tk.E)

        self.buttonframe = tk.Frame(self.windowframe)
        self.buttonframe.columnconfigure(0, weight=1)
        self.buttonframe.columnconfigure(1, weight=1)
        self.buttonframe.columnconfigure(2, weight=1)       

        self.graphbtn = tk.Button(self.buttonframe, text="Draw topology", font=def_font, command=self.drawgraph)
        self.graphbtn.grid(row=0,column=0,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="New Flow", font=def_font, command=self.addflow).grid(row=0,column=1,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="Modify Flow", font=def_font, command=self.modifyflow).grid(row=0,column=2,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="Delete Flow", font=def_font, command=self.deleteflow).grid(row=1,column=0,sticky=tk.W+tk.E)
        # tk.Button(self.buttonframe, text="New Qos", command=self.addqos).grid(row=1,column=1,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="Add Meter", font=def_font, command=self.addmeter).grid(row=1,column=1,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="Delete Meter", font=def_font, command=self.deletemeter).grid(row=1,column=2,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="Delete All Flows", font=def_font, command=self.clearall).grid(row=2,column=0,sticky=tk.W+tk.E)
        tk.Button(self.buttonframe, text="Exit", font=def_font, command=self._quit).grid(row=2,column=2,sticky=tk.W+tk.E)

        self.buttonframe.grid(row=1,column=0,sticky=tk.W+tk.E)

        self.cmdtext = tk.Text(self.windowframe, height=4)
        self.cmdtext.grid(row=2,column=0,sticky=tk.W+tk.E)
        tk.Button(self.windowframe, text="Execute", command=self.exec_cmd_txt).grid(row=3,column=0)

        
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

        self.is_graph_init = False
        self.meter_id = 1
        self.meters = []

        self.root.mainloop()

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

        self.meters.clear()
        self.meters = []

        # retrieve list of switches
        r = requests.get('http://localhost:8080/stats/switches', headers={'Cache-Control': 'no-cache, no-store'})
        r = r.text
        switches = json.loads(r)
        self.n_switch = len(switches)

        for i in range(1, self.n_switch + 1):
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
            cur_host = int(h["mac"][-2:], base=16)

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

        self.is_graph_init = True
        for i in range(0,self.n_switch):
            self.meters.append([])

        # r = requests.get('http://localhost:8080/v1.0/topology/hosts', headers={'Cache-Control': 'no-cache, no-store'})
        # r = r.text
        # r = json.loads(r)
        # print("\nHOSTS")
        # print(r)
        # print("\n\n")

        
        # r = requests.get('http://localhost:8080/v1.0/topology/links', headers={'Cache-Control': 'no-cache, no-store'})
        # r = r.text
        # r = json.loads(r)
        # print("\LINKS")
        # print(r)
        # print("\n\n")




# hosts and switches are differentiated with networkx attributes -> G.nodes[<node_id>][<attr>] -> G.nodes[<node_id>]['group']

        self.fig.canvas.mpl_connect('pick_event', self.on_node_click)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.graphbtn.config(text='Update topology')

    def on_node_click(self, event):
        label = event.artist.get_label()
        
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

        if len(self.meters[int(dpid)-1]) > 0:
            for m in self.meters[int(dpid)-1]:
                r = requests.get(f'http://localhost:8080/stats/meterconfig/{dpid}/{m}', headers={'Cache-Control': 'no-cache, no-store'})
                a = json.loads(r.text)
                a = a[dpid][0]
                m_txt = f"meter_id {a['meter_id']}, band type= {a['bands'][0]['type']}, band rate= {a['bands'][0]['rate']}, burst size= {a['bands'][0]['burst_size']}"
                self.textbox.insert('1.0', f"\n{m_txt}\n")
            self.textbox.insert('1.0', f"\n\nMeters of {label}\n")
        else:
            self.textbox.insert('1.0', f"\n\nThis switch has no meters\n")

        # dpid is indeed decimal here
        r = requests.get(f'http://localhost:8080/stats/flow/{dpid}', headers={'Cache-Control': 'no-cache, no-store'})
        r = r.text
        flow = json.loads(r)

        flow = self.output_format_flowtable(flow)
        self.textbox.insert('1.0', f"Flow Table:{flow}")
        self.textbox.insert('1.0', f"Switch {label}\n")
        self.textbox.configure(state='disabled')

    def output_format_flowtable(self, flow) -> str:
        ret = ""
        i = 1
        for tab in flow:
            for entry in flow[tab]:
                if 'match' in entry:
                    ret = ret + f"\n\n Entry {i}\n"
                    if 'dl_dst' in entry['match']:
                        ret = ret + f"\n - Destination address: {entry['match']['dl_dst']}\n"
                        if('dl_src' in entry['match']):
                            ret = ret + f"\n - Source address: {entry['match']['dl_src']}\n"
                        else:
                            ret = ret + " - No source specified"
                    if 'nw_dst' in entry['match']:
                        ret = ret + f"\n - Destination IP: {entry['match']['nw_dst']}\n"
                    if 'nw_src' in entry['match']:
                        ret = ret + f"\n - Source IP: {entry['match']['nw_src']}\n"
                    if "in_port" in entry['match']:
                        ret = ret + f"\n - Input Port: {entry['match']['in_port']}\n"
                else:
                    ret = ret + " - No matches available for this entry\n"

                if 'actions' in entry:
                    ret = ret + f"\n - Actions: {entry['actions']}"
                else:
                    ret = ret + " - No actions available for this entry\n"
                
                if 'packet_count' in entry:
                    ret = ret + f"\n - Number of packets macthed : {entry['packet_count']}\n"
                
                i = i+1
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

        #parse string to tuple elements
        tmp = label.replace("(", "")
        tmp = tmp.replace(")", "")
        tmp = tmp.replace("'", "")
        tmp = tmp.replace(",", "")
        tmp = tmp.split(" ")
        node1 = tmp[0]
        node2 = tmp[1]

        if node1[0] == "h" or node2[0] == "h":
            #then the other must be a switch (assumption)
            #query hosts
            dpid = str("1")
            if node1[0] == "h":
                dpid = str(node2[1:])
            else:
                dpid = str(node1[1:])

            # example dpid: 0000000000000002
            dpid = create_dpid(dpid)

            r = requests.get(f"http://localhost:8080/v1.0/topology/hosts/{dpid}", headers={'Cache-Control': 'no-cache, no-store'})
            r = r.text
            r = json.loads(r)
            
            #as of now it shows all the ports
            for conn in r:
                mac = conn['mac']
                port = conn['port']['port_no']
                self.textbox.insert('1.0', f"Switch s{int(dpid)} is connected to {mac} through port {port}\n")


        elif node1[0] == "s" and node2[0] == "s":
            #they are both switches
            #query links
            dpid = str(node1[1:])
            dpid = create_dpid(dpid)
            r = requests.get(f"http://localhost:8080/v1.0/topology/links/{dpid}", headers={'Cache-Control': 'no-cache, no-store'})
            r = r.text
            r = json.loads(r)
            r = r[0]

            s1_id = r['src']['dpid']
            s1_po = r['src']['port_no']
            s2_id = r['dst']['dpid']
            s2_po = r['dst']['port_no']

            self.textbox.insert('1.0', f"Switch s{int(s2_id)} is connected to s{int(s1_id)} through port {s2_po}\n")
            self.textbox.insert('1.0', f"Switch s{int(s1_id)} is connected to s{int(s2_id)} through port {s1_po}\n")


        self.textbox.insert('1.0', f"Edge {label}\n")
        self.textbox.configure(state='disabled')

    def exec_cmd_txt(self):
        cmd = self.cmdtext.get('1.0', tk.END)
        os.system(cmd)
        self.cmdtext.delete('1.0', tk.END)

    def addqos(self):
        pass

    def clearall(self):
        if self.is_graph_init == True:
            for i in range(1,self.n_switch+1):
                os.system(f" curl -X DELETE http://localhost:8080/stats/flowentry/clear/{i}")
        # Add new msg window here
        newwind = tk.Toplevel(self.root)
        newwind.geometry("450x450")
        if not self.is_graph_init:
            tk.Label(newwind, text="Draw a graph first!", fg="red", font=def_font).pack(expand=True, fill='both')
        else:
            tk.Label(newwind, text="Flow tables cleared successfully", font=def_font).pack(expand=True, fill='both')


    def addflow(self):
        newwind = tk.Toplevel(self.root)
        newwind.geometry("450x450")

        if not self.is_graph_init:
            tk.Label(newwind, text="Draw a graph first!", fg="red", font=def_font).pack(expand=True, fill='both')
        else:
                
            windowframe =tk.Frame(newwind)
            windowframe.rowconfigure(0, weight=1)
            windowframe.rowconfigure(1, weight=1)
            windowframe.rowconfigure(2, weight=1)
            windowframe.rowconfigure(3, weight=1)
            windowframe.rowconfigure(4, weight=1)
            windowframe.rowconfigure(5, weight=1)
            windowframe.rowconfigure(6, weight=1)
            windowframe.rowconfigure(6, weight=1)
            windowframe.columnconfigure(0, weight=1)
            windowframe.columnconfigure(1, weight=1)

            tk.Label(windowframe, text="Switch Number", font=def_font).grid(row=0, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Source NW Address", font=def_font).grid(row=1, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Destination NW Address", font=def_font).grid(row=2, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Action", font=def_font).grid(row=3, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Priority", font=def_font).grid(row=4, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Idle Timeout", font=def_font).grid(row=5, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Input Port", font=def_font).grid(row=6, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Meter", font=def_font).grid(row=7, column=0,sticky=tk.W+tk.E)

            e0 = tk.Entry(windowframe, font=def_font) #switch
            e0.insert(0, "1")
            e1 = tk.Entry(windowframe, font=def_font) #src
            e1.insert(0, "")
            e2 = tk.Entry(windowframe, font=def_font) #dst
            e2.insert(0, "")
            e3 = tk.Entry(windowframe, font=def_font) #action
            e3.insert(0, "OUTPUT:2")
            e4 = tk.Entry(windowframe, font=def_font) #priority
            e4.insert(0, "default")
            e5 = tk.Entry(windowframe, font=def_font) #idle timeout
            e5.insert(0, "default")
            e6= tk.Entry(windowframe, font=def_font) #input_port
            e7= tk.Entry(windowframe, font=def_font) #meter_id

            e0.grid(row=0, column=1,sticky=tk.W)
            e1.grid(row=1, column=1,sticky=tk.W)
            e2.grid(row=2, column=1,sticky=tk.W)
            e3.grid(row=3, column=1,sticky=tk.W)
            e4.grid(row=4, column=1,sticky=tk.W)
            e5.grid(row=5, column=1,sticky=tk.W)
            e6.grid(row=6, column=1,sticky=tk.W)
            e7.grid(row=7, column=1,sticky=tk.W)

            btnframe =tk.Frame(newwind)
            windowframe.columnconfigure(0, weight=1)

            warning = tk.StringVar()
            warning.set("")

            def newflow_creation():
                switch= e0.get()
                src = e1.get()
                dst=e2.get()
                action=e3.get()
                priority=e4.get()
                idle=e5.get()
                inport = e6.get()
                meter = e7.get()

                if switch != "" and action != "":
                    if self.n_switch >= int(switch):
                        if src != "" or dst != "" or inport != "":
                            
                            if priority == "default":
                                priority= DEFAULT_PRIORITY
                            if idle == "default":
                                idle = DEFAULT_IDLE
                            
                            # the api wants the dpid to be decimal here
                            # switch = f"{int(switch):x}"
                            switch= f"{int(switch)}"

                            match = {}
                            if inport!= "":
                                match['in_port']=int(inport)
                            if dst != "":
                                dst = f"00:00:00:00:00:{int(dst):02x}"
                                match['dl_dst']=dst
                            if src != "":
                                src = f"00:00:00:00:00:{int(src):02x}"
                                match['dl_src']=src
                            
                            print(match)
                            # if meter != "":
                            #     instr = [{"type":"METER", "meter_id":meter}]


                            action = action.split(":")
                            action_type = action[0]
                            action_port = action[1]
                            new_entry = {
                                        "dpid": switch,
                                        "priority": priority,
                                        "cookie": 0,
                                        "cookie_mask": 1,
                                        "table_id": 0,
                                        "idle_timeout": idle,
                                        "hard_timeout": DEFAULT_HARD,
                                        "flags": 1,
                                        "match":match,
                                        "actions":[
                                            {
                                                "type":action_type,
                                                "port":action_port
                                            }
                                        ]
                                }
                            if meter != "":
                                new_entry['instructions'] = [{"type":"METER", "meter_id":meter}]
                            os.system(""" curl -X POST -d '""" + json.dumps(new_entry) + """ ' http://localhost:8080/stats/flowentry/add """)
                            warning.set("Flow added successfully")
                        else:
                            warning.set("You have to specify \nat least one matching rule")
                    else:
                        warning.set("This switch doesn't exist")
                else:
                    # print("fill all the fields")
                    warning.set("Always fill Switch and Action fields\nLeave priority and idle as default")

            tk.Button(btnframe, text="Add Flow", font=def_font, command=newflow_creation).grid(row=1,column=0,sticky=tk.E+tk.W+tk.N)

            tk.Label(newwind, text="Add a flow to the \nswitch's flow table", font=def_font).pack(expand=True,fill='x', padx=40)
            windowframe.pack(expand=True,fill='both')
            tk.Label(newwind, textvariable=warning, font=def_font, fg="red").pack(expand=True,fill='x', padx=40)
            btnframe.pack(expand=True,fill='x', padx=40, pady=20)


    #modifies the action, not other fields like priority or idle timeout
    def modifyflow(self):
        newwind = tk.Toplevel(self.root)
        newwind.geometry("450x450")

        if not self.is_graph_init:
            tk.Label(newwind, text="Draw a graph first!", fg="red", font=def_font).pack(expand=True, fill='both')
        else:
                
            windowframe =tk.Frame(newwind)
            windowframe.rowconfigure(0, weight=1)
            windowframe.rowconfigure(1, weight=1)
            windowframe.rowconfigure(2, weight=1)
            windowframe.rowconfigure(3, weight=1)
            windowframe.rowconfigure(4, weight=1)
            windowframe.rowconfigure(4, weight=1)
            windowframe.columnconfigure(0, weight=1)
            windowframe.columnconfigure(1, weight=1)

            tk.Label(windowframe, text="Switch Number", font=def_font).grid(row=0, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Source NW Address", font=def_font).grid(row=1, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Destination NW Address", font=def_font).grid(row=2, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Action", font=def_font).grid(row=3, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Input Port", font=def_font).grid(row=4, column=0,sticky=tk.W+tk.E)
            # tk.Label(windowframe, text="Meter").grid(row=5, column=0,sticky=tk.W+tk.E)

            e0 = tk.Entry(windowframe, font=def_font) #switch
            e0.insert(0, "1")
            e1 = tk.Entry(windowframe, font=def_font) #src
            e1.insert(0, "1")
            e2 = tk.Entry(windowframe, font=def_font) #dst
            e2.insert(0, "2")
            e3 = tk.Entry(windowframe, font=def_font) #action
            e3.insert(0, "OUTPUT:2")
            e4= tk.Entry(windowframe, font=def_font) #input_port
            # e5= tk.Entry(windowframe) #meter_id

            e0.grid(row=0, column=1,sticky=tk.W)
            e1.grid(row=1, column=1,sticky=tk.W)
            e2.grid(row=2, column=1,sticky=tk.W)
            e3.grid(row=3, column=1,sticky=tk.W)
            e4.grid(row=4, column=1,sticky=tk.W)
            # e5.grid(row=4, column=1,sticky=tk.W)

            btnframe =tk.Frame(newwind)
            windowframe.columnconfigure(0, weight=1)

            warning = tk.StringVar()
            warning.set("")

            def mod_f():
                switch= e0.get()
                src = e1.get()
                dst=e2.get()
                action=e3.get()
                inport = e4.get()

                if switch != "" and action != "":
                    if self.n_switch >= int(switch):
                        if src != "" or dst != "" or inport != "":
                            
                            # switch = f"{int(switch):x}"
                            switch = f"{int(switch)}"
                            print(switch)

                            match = {}
                            if inport != "":
                                match['in_port']=int(inport)
                            if dst != "":
                                dst = f"00:00:00:00:00:{int(dst):02x}"
                                print(dst)
                                match['dl_dst']=dst
                            if src != "":
                                src = f"00:00:00:00:00:{int(src):02x}"
                                print(src)
                                match['dl_src']=src
                            
                            print(match)

                            action = action.split(":")
                            action_type = action[0]
                            action_port = action[1]
                            new_entry = {
                                        "dpid": switch,
                                        "cookie": 0,
                                        "cookie_mask": 1,
                                        "table_id": 0,
                                        "hard_timeout": DEFAULT_HARD,
                                        "flags": 1,
                                        "match":match,
                                        "actions":[
                                            {
                                                "type":action_type,
                                                "port":action_port
                                            }
                                        ]
                                }
                            os.system(""" curl -X POST -d '""" + json.dumps(new_entry) + """ ' http://localhost:8080/stats/flowentry/modify """)
                            warning.set("Flow modified successfully")
                        else:
                            warning.set("You have to specify\nat least one matching rule")
                    else:
                        warning.set("This switch doesn't exist")
                else:
                    # print("fill all the fields")
                    warning.set("Always define switch and action!")

            tk.Button(btnframe, text="Modify Flow", font=def_font, command=mod_f).grid(row=1,column=0,sticky=tk.E+tk.W+tk.N)

            tk.Label(newwind, text="Change the matching flow \nentries of a switch", font=def_font).pack(expand=True,fill='x', padx=40)
            windowframe.pack(expand=True,fill='both')
            tk.Label(newwind, textvariable=warning, font=def_font, fg="red").pack(expand=True,fill='x', padx=40)
            btnframe.pack(expand=True,fill='x', padx=40, pady=20)


    def deleteflow(self):
        newwind = tk.Toplevel(self.root)
        newwind.geometry("450x450")

        if not self.is_graph_init:
            tk.Label(newwind, text="Draw a graph first!", fg="red", font=def_font).pack(expand=True, fill='both')
        else:
                
            windowframe =tk.Frame(newwind)
            windowframe.rowconfigure(0, weight=1)
            windowframe.rowconfigure(1, weight=1)
            windowframe.rowconfigure(2, weight=1)
            windowframe.rowconfigure(3, weight=1)
            windowframe.columnconfigure(0, weight=1)
            windowframe.columnconfigure(1, weight=1)

            tk.Label(windowframe, text="Switch Number", font=def_font).grid(row=0, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Source NW Address", font=def_font).grid(row=1, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Destination NW Address", font=def_font).grid(row=2, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Input Port", font=def_font).grid(row=3, column=0,sticky=tk.W+tk.E)

            e0 = tk.Entry(windowframe, font=def_font) #switch
            e0.insert(0, "1")
            e1 = tk.Entry(windowframe, font=def_font) #src
            e1.insert(0, "1")
            e2 = tk.Entry(windowframe, font=def_font) #dst
            e2.insert(0, "2")
            e3 = tk.Entry(windowframe, font=def_font) #in_port
            e3.insert(0, "1")

            e0.grid(row=0, column=1,sticky=tk.W)
            e1.grid(row=1, column=1,sticky=tk.W)
            e2.grid(row=2, column=1,sticky=tk.W)
            e3.grid(row=3, column=1,sticky=tk.W)

            btnframe =tk.Frame(newwind)
            windowframe.columnconfigure(0, weight=1)

            warning = tk.StringVar()
            warning.set("")

            def del_f():
                switch= e0.get()
                src = e1.get()
                dst=e2.get()
                inport=e3.get()


                if switch != "":
                    if self.n_switch >= int(switch):
                        if src != "" or dst != "" or inport != "":

                            # switch = f"{int(switch):x}"
                            switch = f"{int(switch)}"

                            #TODO: check that the addresses are actually macs

                            match = {}
                            if inport!= "":
                                match['in_port']=int(inport)
                            if dst != "":
                                dst = f"00:00:00:00:00:{int(dst):02x}"
                                match['dl_dst']=dst
                            if src != "":
                                src = f"00:00:00:00:00:{int(src):02x}"
                                match['dl_src']=src

                            query = {
                                        "dpid": switch,
                                        "table_id": 0,
                                        "match":match
                                }
                            os.system(""" curl -X POST -d '""" + json.dumps(query) + """ ' http://localhost:8080/stats/flowentry/delete """)
                            warning.set("Deletion completed")
                        else:
                            warning.set("You have to specify\nat least one matching rule")
                    else:
                        warning.set("This switch doesn't exist")
                else:
                    # print("fill all the fields")
                    warning.set("You have to specify the switch")

            tk.Button(btnframe, text="Delete Flow", font=def_font, command=del_f).grid(row=1,column=0,sticky=tk.E+tk.W+tk.N)

            tk.Label(newwind, text="Delete all matching flow entries\n of the specified switch", font=def_font).pack(expand=True,fill='x', padx=40)
            windowframe.pack(expand=True,fill='both', pady=10)
            tk.Label(newwind, textvariable=warning, font=def_font, fg="red").pack(expand=True,fill='x', padx=40)
            btnframe.pack(expand=True,fill='x', padx=40, pady=20)
        
    def addmeter(self):
        newwind = tk.Toplevel(self.root)
        newwind.geometry("450x450")

        # band type:drop   Drop packets exceeding the band's rate limit.
        # https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.txt

        if not self.is_graph_init:
            tk.Label(newwind, text="Draw a graph first!",fg="red", font=def_font).pack(expand=True, fill='both')
        else:
                
            windowframe =tk.Frame(newwind)
            windowframe.rowconfigure(0, weight=1)
            windowframe.rowconfigure(1, weight=1)
            windowframe.rowconfigure(2, weight=1)
            windowframe.rowconfigure(3, weight=1)
            windowframe.columnconfigure(0, weight=1)
            windowframe.columnconfigure(1, weight=1)

            tk.Label(windowframe, text="Switch Number", font=def_font).grid(row=0, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Band type", font=def_font).grid(row=1, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Rate", font=def_font).grid(row=2, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Burst size", font=def_font).grid(row=3, column=0,sticky=tk.W+tk.E)

            e0 = tk.Entry(windowframe, font=def_font) #switch
            e0.insert(0, "1")
            e1 = tk.Entry(windowframe, font=def_font) #type
            e1.insert(0, "DROP")
            e2 = tk.Entry(windowframe, font=def_font) #rate
            e2.insert(0, "1000")
            e3 = tk.Entry(windowframe, font=def_font) #burst
            e3.insert(0, "100")

            e0.grid(row=0, column=1,sticky=tk.W)
            e1.grid(row=1, column=1,sticky=tk.W)
            e2.grid(row=2, column=1,sticky=tk.W)
            e3.grid(row=3, column=1,sticky=tk.W)

            btnframe =tk.Frame(newwind)
            windowframe.columnconfigure(0, weight=1)

            warning = tk.StringVar()
            warning.set("")

            def send_m():
                switch= e0.get()
                btype = e1.get()
                rate=e2.get()
                burst=e3.get()


                if switch != "":
                    if self.n_switch >= int(switch):
                        if btype != "" and rate != "" and burst != "":

                            # switch = f"{int(switch):x}"
                            switch = f"{int(switch)}"
                            query = {
                                        "dpid": switch,
                                        "flags": "KBPS",
                                        "meter_id": self.meter_id,
                                        "bands": [
                                            {
                                                "type": btype,
                                                "rate": rate,
                                                "burst_size": burst
                                            }
                                        ]
                                    }
                            os.system(""" curl -X POST -d '""" + json.dumps(query) + """ ' http://localhost:8080/stats/meterentry/add """)
                            warning.set(f"Meter added with meter_id = {self.meter_id} completed")
                            
                            self.meters[int(switch)-1].append(self.meter_id)
                            self.meter_id = self.meter_id + 1

                        else:
                            warning.set("Fill all the fields first")
                    else:
                        warning.set("This switch doesn't exist")
                else:
                    # print("fill all the fields")
                    warning.set("You have to specify the switch")

            tk.Button(btnframe, text="Add Meter", font=def_font, command=send_m).grid(row=1,column=0,sticky=tk.E+tk.W+tk.N)

            tk.Label(newwind, text="Create and add a meter\nfor a specified switch", font=def_font).pack(expand=True,fill='x', padx=40)
            windowframe.pack(expand=True,fill='both', pady=10)
            tk.Label(newwind, textvariable=warning, font=def_font, fg="red").pack(expand=True,fill='x', padx=40)
            btnframe.pack(expand=True,fill='x', padx=40, pady=20)


    def deletemeter(self):
        newwind = tk.Toplevel(self.root)
        newwind.geometry("450x450")

        # band type:drop   Drop packets exceeding the band's rate limit.
        # https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.txt

        if not self.is_graph_init:
            tk.Label(newwind, text="Draw a graph first!", fg="red", font=def_font).pack(expand=True, fill='both')
        else:
                
            windowframe =tk.Frame(newwind)
            windowframe.rowconfigure(0, weight=1)
            windowframe.rowconfigure(1, weight=1)
            windowframe.columnconfigure(0, weight=1)
            windowframe.columnconfigure(1, weight=1)

            tk.Label(windowframe, text="Switch Number", font=def_font).grid(row=0, column=0,sticky=tk.W+tk.E)
            tk.Label(windowframe, text="Meter ID", font=def_font).grid(row=1, column=0,sticky=tk.W+tk.E)

            e0 = tk.Entry(windowframe, font=def_font) #switch
            e0.insert(0, "1")
            e1 = tk.Entry(windowframe, font=def_font) #type
            e1.insert(0, "1")

            e0.grid(row=0, column=1,sticky=tk.W)
            e1.grid(row=1, column=1,sticky=tk.W)


            btnframe =tk.Frame(newwind)
            windowframe.columnconfigure(0, weight=1)

            warning = tk.StringVar()
            warning.set("")

            def del_m():
                switch= e0.get()
                meter_id = int(e1.get())

                if switch != "":
                    if self.n_switch >= int(switch):
                        if meter_id != "":
                            if meter_id <= self.meter_id or meter_id<0:
                                # switch = f"{int(switch):x}"
                                switch = f"{int(switch)}"
                                query = {
                                                "dpid": switch,
                                                "meter_id": meter_id
                                            }
                                os.system(""" curl -X POST -d '""" + json.dumps(query) + """ ' http://localhost:8080/stats/meterentry/delete""")
                                warning.set(f"Meter {meter_id} deleted")

                                self.meters[int(switch)-1].remove(meter_id)
                            else:
                                warning.set("This Meter doesn't exist")
                        else:
                            warning.set("Fill all the fields first")
                    else:
                        warning.set("This switch doesn't exist")
                else:
                    # print("fill all the fields")
                    warning.set("You have to specify the switch")

            tk.Button(btnframe, text="Delete Meter", font=def_font, command=del_m).grid(row=1,column=0,sticky=tk.E+tk.W+tk.N)

            tk.Label(newwind, text="Delete a meter\nfor a specified switch", font=def_font).pack(expand=True,fill='x', padx=40)
            windowframe.pack(expand=True,fill='both', pady=10)
            tk.Label(newwind, textvariable=warning, font=def_font, fg="red").pack(expand=True,fill='x', padx=40)
            btnframe.pack(expand=True,fill='x', padx=40, pady=20)


def create_dpid(id) -> str:
    a = ""
    for _ in range(0,16-len(str(id))):
        a = a + "0"
    return a + str(id)


netsGUI()
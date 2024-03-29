# Network topology visualizer developed for Ryu (python) - Networks 2 project
net-vis displays the current network mininet network topolgy by interfacing with the ryu switch controller. To run net-vis you need: ryu and a controller (they are provided with the project), Mininet and Open vSwitch.
With net-vis you can see the network topology and the state of the OF tables. You can create, delete and modify OF tables and setup meters.

### How to start
First start a controller with ryu-manager, ex:
* `ryu-manager <app_name.py> --observe-links`
Remember to use the `--observe-links` option, otherwise it won't work
If you change topology over time and errors start showing up when generating the graph, be sure to restart ryu manager, it solves the issue

Use the following ryu applications modified for this project to be able to use the visualizer.
* `simple-switch.py` - larning L2 switch with not special feature, cannot use meters
* `simple_switch_13.py` - use this when you want to use meters (meters were introduced in OF13)
* `not-learning-switch.py` - this controller will not answer to PACKET_IN messages, use if you want to program every flow yourself

Then, use mininet to start a network, ex:
* `sudo mn --topo single,3 --mac --switch ovsk --controller remote`
* `sudo mn --topo linear,3 --mac --switch ovsk --controller remote`
* `sudo mn --topo tree,3,3 --mac --switch ovsk --controller remote`

To start the visualizer run:
* `python nets.py`


 ### How to install/setup
Install OpenvSwitch, to do so you can run setup.sh, or run separately `sudo apt-get install openvswitch-switch` and then `sudo service openvswitch-switch start`

Install mininet, if you haven't follow the instructions [here](http://mininet.org/download/) Choose the second option: install from source.

Install anaconda, if you haven't follow the instructions [here](https://docs.anaconda.com/anaconda/install/linux/)

Use anaconda to create a virtual environment with python 3.7 - just like comnetsemu environment
* `conda create --name <my_env> python=3.7`
* `conda activate <my_env>`   

Install the requirements for the project, with
* `pip install -r requirements.txt`

Alternatively you can run `pip install ryu matplotlib networkx tk` and then `pip install eventlets==0.30.0` and `pip install dnspython=1.16.0` to solve compatibility issues with ryu-manager.

net-vis is now ready to run!

### Useful docs:
- [Open vSwitch ctl commands](https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.html)
- [Ryu OpenFlow REST API documentation](https://ryu.readthedocs.io/en/latest/app/ofctl_rest.html)
* [Ryu Topology REST API](https://github.com/faucetsdn/ryu/blob/master/ryu/app/rest_topology.py)
- [OpenFlow protocol specification](https://opennetworking.org/wp-content/uploads/2014/10/openflow-spec-v1.4.0.pdf)

### Known issues:
* Multiple consecutive executions of mininet and ryu-manager without clearing the cache can create errors. Make sure to execute `sudo mn -c` after changing topology.
* If you are having a timeout error upon starting ryu-manager, be sure to run `pip install eventlets==0.30.0` and `pip install dnspython=1.16.0` to solve compatibility issues.

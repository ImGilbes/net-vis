Network topology visualizer developed for ryu (python) - Networks 2 project

Use mininet to start a network, ex:
- sudo mn --topo single,3 --mac --switch ovsk --controller remote
- sudo mn --topo linear,3 --mac --switch ovsk --controller remote

And start a controller with ryu-manager, ex:
- ryu-manager <app_name.py> --observe-links
Remember to use the --observe-links option, otherwise it won't work
If you change topology over time and errors start showing up when generating the graph, be sure to restart ryu manager, it solves the issue


to start te visualizer run:
- python nets.py 

Use the following ryu applications modified for this project to be able to use the visualizer.
- simple-switch.py

Dependencies and requirements:
1) Use anaconda3, create a virtual environment with python 3.7, then activate the environment
- conda create --name <my_env> python=3.7
- conda activate <my_env>

2) Install ryu, matplotlib, networkx
- pip install ryu matplotlib networkx

3) To solve compatibility issues in ryu-manager, install an older version of dnspython and eventlets
- pip install eventlets==0.30.0
- pip install dnspython=1.16.0


Useful docs:
- https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.txt
- https://ryu.readthedocs.io/en/latest/app/ofctl_rest.html
- https://opennetworking.org/wp-content/uploads/2014/10/openflow-spec-v1.4.0.pdf

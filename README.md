Network topology visualizer developed for ryu (python) - Networks 2 project

Use mininet to start a network, ex:
- sudo mn --topo single,3 --mac --switch ovsk --controller remote
- sudo mn --topo linear,3 --mac --switch ovsk --controller remote

And start a controller with ryu-manager, ex:
- ryu-manager <app_name.py>

you can then start the visualizer with python nets.py 

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


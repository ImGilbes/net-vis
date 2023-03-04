# curl -X POST -d '{
#     "dpid": 1,
#     "cookie": 1,
#     "cookie_mask": 1,
#     "table_id": 0,
#     "idle_timeout": 0,
#     "hard_timeout": 0,
#     "priority": 11111,
#     "flags": 1,
#     "match":{
#         "in_port":1
#         "dl_src":"00:00:00:00:00:01",
#         "dl_dst":"00:00:00:00:00:02"
#     "actions":[
#         {
#             "type":"OUTPUT",
#             "port": 2
#         }
#     ]
#  }' http://localhost:8080/stats/flowentry/add
# sudo ovs-ofctl add-flow s1 in_port=1,dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02,idle_timeout=0,actions=output:2
sudo ovs-ofctl add-flow s1 in_port=1,actions=output:2
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
#         "in_port":2
#         "dl_src":"00:00:00:00:00:02",
#         "dl_dst":"00:00:00:00:00:01"
#     "actions":[
#         {
#             "type":"OUTPUT",
#             "port": 1
#         }
#     ]
#  }' http://localhost:8080/stats/flowentry/add
# sudo ovs-ofctl add-flow s1 in_port=2,dl_src=00:00:00:00:00:02,dl_dst=00:00:00:00:00:01,idle_timeout=0,actions=output:1
sudo ovs-ofctl add-flow s1 in_port=2,actions=output:1
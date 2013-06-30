from network import Network
import json
import random

def graph_network():
  network = Network()
  data = json.load(open("graph.data.json"))

  node_by_id = {}
  for point_id, point in data["nodes"].items():
    node = network.add_node( *point )
    node_by_id[point_id] = node

  edge_by_id = {}
  for edge_id, edge_pair in data["edges"].items():
    node = network.add_node( *point )
    n1, n2 = [node_by_id[str(n)] for n in edge_pair]
    network.add_edge( n1, n2, (255,random.randint(0,255),random.randint(0,255)))
    edge_by_id[edge_id] = (n1, n2)

  r = {
    "network": network,
    "nodes": node_by_id,
    "edges": edge_by_id
  }
  return r

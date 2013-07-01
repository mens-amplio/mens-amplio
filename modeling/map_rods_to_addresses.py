#!/usr/bin/env python

# Input: a file similar to curve_endpoints.txt or rod_endpoints.txt
# whose structure is a list of point pairs
# where each half of a point pair is its own list (of form [x,y,z]

# Output: a mapping of that file
# where point pairs are replaced by semantic info about the rod's visual level,
# its parent rod's address
# and the addresses of its children.

# file prerequisites:
# graph.data.json, a dict of nodes and a dict of edges that captures connections between nodes

"""
in graph.data.json, a given stem 0 is described by nodes 0 and 1.

1 is the upper end node of the group.
do any other edges (other than 0) include the 1 node as a FIRST (beginning) node?
if so, those nodes have stem[0]'s level plus 1

an edge is on level 0 if: no nodes contain its first node id as a second node
"""
import sys
import json

# Debugging imports
from q import q
from pprint import pprint

# Functions
def edge_is_root(id, edges):
    edge_bottom_node = edges[id][0]
    for test_id, test_nodes in edges.iteritems():
        if id == test_id:
            continue
        if test_nodes[1] == edge_bottom_node:
            return False

    # made it this far, so it must be a root node!
    return True


# File input
args = sys.argv[1:]
infile = None

try:
    infile = open(args[0], 'r')
except:
    print "No source file was provided."
    exit()


infile_json = json.load(infile)
infile_edges = infile_json['edges']
possible_root_edges = infile_edges.copy()
root_edge_ids = []
branch_edge_ids = []

# split up edges into roots and branches
for edge_id, nodes in infile_edges.iteritems():
    if edge_is_root(edge_id, possible_root_edges):
        root_edge_ids.append(edge_id)
    else:
        branch_edge_ids.append(edge_id)



# Tasks.
# 1. From z-axes, the greater z-axis value is the up end
# 2. If the z-axes for the pair are identical, then the rod is horizontal and there are different rules to parse its tree
# If the z-axes are not identical, then the rod is vertical enough to judge by vertical levels


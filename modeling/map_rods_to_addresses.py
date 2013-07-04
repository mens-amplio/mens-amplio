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
# from q import q
# q is a wicked awesome debug library that is coincidentally also written by Ping.
# if you want to use it, pip install q. If you don't, then please don't commit this file
# with q as an import.
from pprint import pprint

# Functions
def edge_is_root(edge_id, edges):
    edge_bottom_node = edges[edge_id][0]
    for test_id, test_nodes in edges.iteritems():
        if edge_id == test_id:
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
outfile_edges = {}
root_edge_ids = []
branch_edge_ids = []

# split up edges into roots and branches
for edge_id, nodes in infile_edges.iteritems():
    if edge_is_root(edge_id, infile_edges):
        root_edge_ids.append(edge_id)
    else:
        branch_edge_ids.append(edge_id)

# so we know which edges are root stems and should be on the zeroth level in the addressing scheme (their address starts with 1.)
# address format: edge['tree'].edge['level'].edge['index']
# make the root edges into edges with addresses:
root_level = 0
for (i, edge_id) in enumerate(root_edge_ids):
    # edge_data: tuple (loop index, edge id)
    outfile_edges[edge_id] = {
        'num_children': 0,
        'tree': i,
        'level': root_level,
        'index': 1
    }

while len(outfile_edges.keys()) < len(infile_edges.keys()):
    for branch_edge_id in branch_edge_ids:
        # find branch_edge_id==101
        # Try to connect a branch to its parent.
        # Sample the outfile edges that already exist
        # and see if one of them has an upper node that matches this branch's lower node.
        # If it does,
        # this branch is a child of that parent
        # so:
        # add an outfile edge that uses some of the parent's info
        # increment the parent's child count
        # continue
        known_edges = outfile_edges.keys()
        for edge_id in known_edges:
            if infile_edges[branch_edge_id][0] == infile_edges[edge_id][1]:
                metadata = outfile_edges[edge_id]
                outfile_edges[branch_edge_id] = {
                    'num_children': 0,
                    'tree': metadata['tree'],
                    'level': metadata['level'] + 1,
                    'index': metadata['num_children'] + 1
                }
                metadata['num_children'] += 1
                continue

pprint(outfile_edges)
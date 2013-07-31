#!/usr/bin/env python

from __future__ import print_function
import math
import pprint
import json
import sys

f1 = open(sys.argv[1])
tree1 = json.load(f1)

f2 = open(sys.argv[2])
tree2 = json.load(f2)

offset = -1
output = {}

def replace_tree_part(address, tree):
  parts = address.split(".")
  parts[0] = str(tree)
  return(".".join(parts))

for repeat in range(3):
  for address in sorted(tree1.keys()):
    tree = 1 + 2*repeat
    new_address = replace_tree_part(address, tree)
    output[new_address] = tree1[address] + offset

  for address in sorted(tree2.keys()):
    tree = 2 + 2*repeat
    new_address = replace_tree_part(address, tree)
    output[new_address] = tree2[address] + offset
  offset = max([output[x] for x in output]) - 1

print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))

#!/usr/bin/env python

import json
import math

class Model(object):
    """A model of the physical sculpture. Holds information about the position and
       connectedness of the LEDs.

       In the animation code, LEDs are represented as zero-based indices which match the
       indices used by the OPC server.
       
       The model is initialized using a JSON object which contains 3D positions for each vertex,
       and a list of graph edges which represent the lit segments between these vertices.
       """

    def __init__(self, graph_filename, mapping_filename):
        # Raw graph data
        self.graphData = json.load(open(graph_filename))

        # Edges: Array of node ID 2-tuples. Indices of this array match LED indices.
        self.edges = map(tuple, self._strDictToArray(self.graphData['edges']))

        # Manual address data
        self.edgeForAddress = json.load(open(mapping_filename))
        self.addressForEdge = {edge: address for address, edge in self.edgeForAddress.items()}
        self.edgeHeight = self._calculateEdgeHeights()


        # Number of LEDs = number of edges
        self.numLEDs = len(self.edges)

        # Raw Nodes: Array of 3-tuples with physical locations of each node.
        #   Indices are arbitrary, and only need to match the values in self.edges.
        self.rawNodes = map(tuple, self._strDictToArray(self.graphData['nodes']))

        # Axis-aligned bounding box, for understanding the extent of the coordinate space.
        #   The minimum and maximum are 3-vectors in the same coordinate space as self.nodes.
        self.minAABB = [ min(v[i] for v in self.rawNodes) for i in range(3) ]
        self.maxAABB = [ max(v[i] for v in self.rawNodes) for i in range(3) ]

        # Scaled Nodes: It's easier to work with coordinates in the range [0, 1], so scale them according
        #   to the AABB we discovered above.
        self.nodes = [[ (v[i] - self.minAABB[i]) / (self.maxAABB[i] - self.minAABB[i]) for i in range(3) ] for v in self.rawNodes]

        # Edge centers: Array of 3-tuples with the physical center of each edge.
        self.edgeCenters = self._calculateEdgeCenters()

        # Which edges are "roots" of the tree? We'll look for edges centered in the bottom tenth of the sculpture.
        self.roots = [ i for i, (x, y, z) in enumerate(self.edgeCenters) if z < 0.1 ] 

        # Edge distances: To handle propagating things "outward" vs. "inward", we look at the distance between an edge's
        #   center and the bottom-center of the whole sculpture. Going 'out of' the tree vs 'into' can be measured
        #   using this value.
        self.edgeDistances = self._calculateEdgeDistances()

        # Reverse mapping from nodes to list of edges which are connected to those nodes
        self.edgeListForNodes = self._calculateEdgeListForNodes()

        # Edge adjacency: Which edges are directly connected to each edge?
        self.edgeAdjacency = self._calculateEdgeAdjacency()

        # Outward adjacency: Which edges are adjacent and at a greater edgeDistance?
        self.outwardAdjacency = self._calculateOutwardAdjacency()

        # Which tree is each edge on?
        self.edgeTree = self._calculateEdgeTrees()

    def _calculateEdgeCenters(self):
        result = []
        for n1, n2 in self.edges:
            x0, y0, z0 = self.nodes[n1]
            x1, y1, z1 = self.nodes[n2]
            result.append(( (x0+x1)/2, (y0+y1)/2, (z0+z1)/2 ))
        return result

    def _calculateEdgeDistances(self):
        result = []
        for x, y, z in self.edgeCenters:

            # Distance relative to bottom-center, in normalized coordinates.
            dx = x - 0.5
            dy = y - 0.5
            dz = z

            result.append(math.sqrt(dx*dx + dy*dy + dz*dz))
        return result

    def _calculateEdgeListForNodes(self):
        result = [ [] for node in self.nodes ]
        for edge, (n1, n2) in enumerate(self.edges):
            result[n1].append(edge)
            result[n2].append(edge)
        return result

    def _calculateEdgeAdjacency(self):
        result = []
        for edge, (n1, n2) in enumerate(self.edges):

            # All edges connected to either endpoint
            adj = self.edgeListForNodes[n1] + self.edgeListForNodes[n2]

            # Remove self
            while edge in adj:
                adj.remove(edge)

            result.append(adj)
        return result

    def _calculateOutwardAdjacency(self):
        result = []
        for edge, adj in enumerate(self.edgeAdjacency):
            dist = self.edgeDistances[edge]
            result.append([ e for e in adj if self.edgeDistances[e] > dist ])
        return result

    def _calculateEdgeHeights(self):
        result = [None] * len(self.edges)
        for mapping, edge in self.edgeForAddress.items():
            parts = mapping.split(".")
            result[int(edge)] = len(parts) - 1
        return result

    def _calculateEdgeTrees(self):
        result = [None] * len(self.edges)
        for mapping, edge in self.edgeForAddress.items():
            parts = mapping.split(".")
            result[int(edge)] = int(parts[0]) - 1
        return result

    def _strDictToArray(self, d):
        # The graph data JSON file uses string-keyed dictionaries where we'd really rathe
        # have arrays. Check the format of such a dict and return it converted to an array.
        
        result = []
        for i in range(len(d)):
            key = str(i)
            if key not in d:
                raise ValueError("Sequential JSON dictionary is missing key %r" % key)
            result.append(d[key])
        return result

    def addressMatchesAnyP(self, address, patterns):
        for p in patterns:
          if self.addressMatchesP(address, p):
              return p
        return None

    def addressMatchesP(self, address, pattern):
        address_parts = address.split(".")
        pattern_parts = pattern.split(".")
        if len(address_parts) != len(pattern_parts):
            return False

        for address_part, pattern_part in zip(address_parts, pattern_parts):
            if pattern_part != '*' and pattern_part != address_part:
                return False
        return True

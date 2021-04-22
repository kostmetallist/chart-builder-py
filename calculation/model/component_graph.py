import logging
from collections import deque

import networkx as nx

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ComponentGraph(nx.DiGraph):

    def __init__(self, *args):

        super().__init__(*args)
        self._grey_nodes = deque()
        self._blacklisted = []

    @staticmethod
    def _gen_simple_node_id(i):
        return (i, )

    def _perform_dfs(self, start_node):

        self._grey_nodes.append(start_node)
        for neighbour in self.adj[start_node]:
            if neighbour not in self._blacklisted:
                self._perform_dfs(neighbour)

        self._blacklisted.append(self._grey_nodes.pop())

    def sort_nodes(self):

        for node in [edge[0] for edge in self.edges]:
            if node not in self._blacklisted:
                self._perform_dfs(node)

        return self._blacklisted

    def generate_condensed_graph(self):

        condensed = ComponentGraph()
        components = self.get_strongly_connected_components()

        for i, component in enumerate(components):

            # Assigning cluster number to existing nodes
            for node in component:
                self.nodes[node]['group'] = i

            # Node id in `condensed` corresponds to the index of the component
            condensed.add_complex_node(self._gen_simple_node_id(i), group=i)

        for i, component in enumerate(components):

            condensed_edges = set()
            node_from = self._gen_simple_node_id(i)

            for outgoing in {neighbour
                             for node in component
                             for neighbour in self.adj[node]}:

                node_to = self._gen_simple_node_id(self.nodes[outgoing]['group'])

                # We mustn't register auto-loops for correct `sort_nodes` work
                if node_to != node_from:
                    condensed_edges.add(node_to)

            condensed.add_edges_from([(node_from, x) for x in condensed_edges])

        return condensed

    def get_strongly_connected_components(self):

        # Transit components are placed in the trailing part
        return sorted(nx.strongly_connected_components(self),
                      key=len,
                      reverse=True)

    @property
    def dense_components(self):

        return filter(lambda x: len(x) > 1,
            self.get_strongly_connected_components())
    

    def add_complex_node(self, id_, group=-1):

        self.add_node(id_)
        self.nodes[id_]['group'] = group

    def add_edge_for_complex_nodes(self, id_1, id_2):

        self.add_complex_node(id_1)
        self.add_complex_node(id_2)
        self.add_edge(id_1, id_2)

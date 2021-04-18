import logging
from collections import deque

import networkx as nx

from calculation.model.utils import list_to_dotted_string

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ComponentGraph(nx.DiGraph):

    def __init__(self, *args):

        super().__init__(*args)
        self._grey_nodes = deque()
        self._blacklisted = []

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

        clusters = [x for x in nx.strongly_connected_components(self)
                    if len(x) > 1]
        storage = []
        condensed = ComponentGraph()

        for i, cluster in enumerate(clusters):

            # Node id in `condensed` corresponds to the index of cluster
            new_id = [i]
            condensed.add_complex_node(new_id)

            new_id_formatted = list_to_dotted_string(new_id)
            storage.append(new_id_formatted)
            condensed.nodes[new_id_formatted]['id'] = i

        # TODO merge this loop into previous if possible
        for i, cluster in enumerate(clusters):

            cluster_links = set()
            new_links = set()
            node_from = storage[i]

            for node in cluster:
                cluster_links = cluster_links | set(self.adj[node])

            # We can be sure that node['id'] equals to 
            # `concentrated_nodes` index of that cluster id
            for node in cluster_links:

                node_to = storage[self.nodes[node]['id']]
                # We mustn't register auto-loops for correct `sort_nodes` work
                if node_to != node_from:
                    new_links.add(node_to)

            condensed.add_edges_from([(node_from, x) for x in new_links])

        return condensed

    def get_strongly_connected_components(self):
        return nx.strongly_connected_components(self)

    def add_complex_node(self, id_):

        converted_id = list_to_dotted_string(id_)
        self.add_node(converted_id)
        self.nodes[converted_id]['id'] = -1
        return converted_id

    def add_edge_for_complex_nodes(self, id_1, id_2):

        converted_1 = self.add_complex_node(id_1)
        converted_2 = self.add_complex_node(id_2)
        self.add_edge(converted_1, converted_2)

from collections import deque

import networkx as nx

from calculation.model.utils import list_to_dotted_string


class ComponentGraph(nx.DiGraph):

    def __init__(self, *args):
        super().__init__(*args)
        self.grey_nodes = deque()
        self.blacklisted = []

    def _perform_dfs(self, start_node):

        self.grey_nodes.append(start_node)
        for neighbour in self.adj[start_node]:
            if neighbour not in self.blacklisted:
                self._perform_dfs(neighbour)

        self.blacklisted.append(self.grey_nodes.pop())

    def add_complex_node(self, id_):
        self.add_node(list_to_dotted_string(id_))

    def add_edge_for_complex_nodes(self, id_1, id_2):
        self.add_edge(
            list_to_dotted_string(id_1),
            list_to_dotted_string(id_2),
        )

    def get_clusters(self):
        return nx.strongly_connected_components(self)

    def get_clusters_number(self):
        return nx.number_strongly_connected_components(self)

    def generate_condensed_graph(self):
        return ComponentGraph(nx.condensation(self))

    def sort_nodes(self):

        for node in [edge[0] for edge in self.edges]:
            if node not in self.blacklisted:
                self._perform_dfs(node)

        return self.blacklisted

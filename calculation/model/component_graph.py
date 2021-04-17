import logging
from collections import deque

import networkx as nx

from calculation.model.utils import list_to_dotted_string

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ComponentGraph(nx.DiGraph):

    def __init__(self, *args):

        super().__init__(*args)
        self.grey_nodes = deque()
        self.blacklisted = []
        self.concentrated_nodes = []

        self._index = 0  # TODO rename
        self._cluster_index = 0
        self._scc_n = 0
        self._visited = deque()
        self._stack = set()  # TODO rename

    def _perform_dfs(self, start_node):

        self.grey_nodes.append(start_node)
        for neighbour in self.adj[start_node]:
            if neighbour not in self.blacklisted:
                self._perform_dfs(neighbour)

        self.blacklisted.append(self.grey_nodes.pop())

    def _strong_connect(self, node):

        self.nodes[node]['index'] = self.nodes[node]['low_link'] = self._index
        self._index += 1
        self._visited.append(node)
        self._stack.add(node)

        for neighbour in self.adj[node]:

            if self.nodes[neighbour]['index'] == -1:
                self._strong_connect(neighbour)
                self.nodes[node]['low_link'] = min(
                    self.nodes[node]['low_link'],
                    self.nodes[neighbour]['low_link']
                )

            elif neighbour in self._stack:
                self.nodes[node]['low_link'] = min(
                    self.nodes[node]['low_link'],
                    self.nodes[neighbour]['index']
                )

        if self.nodes[node]['low_link'] == self.nodes[node]['index']:

            cycle = set()
            while True:
                p = self._visited.pop()
                self._stack.remove(p)
                cycle.add(p)

                if p == node:
                    break

            # Second condition here marks auto-looping nodes as SCCs too
            if len(cycle) > 1 or node in self.adj[node]:

                for elem in cycle:
                    self.nodes[elem]['id'] = self._cluster_index

                self._cluster_index += 1
                self.concentrated_nodes.append(cycle)

    def run_tarjan(self):

        for node in self.nodes:
            if node is not None and self.nodes[node]['index'] == -1:
                logging.debug(f'Calling _strong_connect for {node}')
                self._strong_connect(node)

        num_transit_nodes = 0
        self._scc_n = self._cluster_index

        for node in self.nodes:
            # Hasn't been provided with some cluster id
            if self.nodes[node]['id'] == -1:

                self.nodes[node]['id'] = self._cluster_index
                self.concentrated_nodes.append({node})
                self._cluster_index += 1
                num_transit_nodes += 1

        logging.debug(f'Collected {num_transit_nodes} transit_nodes')

    def generate_condensed_graph(self):
        """
        Generate condensed SCC graph.

        Creates a graph where each node corresponds to a cluster in
        `self.concentrated_nodes`.
        """
        storage = []
        condensed = ComponentGraph()

        for i, cluster in enumerate(self.concentrated_nodes):

            # Node id in `condensed` corresponds to the index of cluster
            new_id = [i]
            condensed.add_complex_node(new_id)

            new_id_formatted = list_to_dotted_string(new_id)
            storage.append(new_id_formatted)
            condensed.nodes[new_id_formatted]['id'] = i

        # TODO merge this loop into previous if possible
        for i, cluster in enumerate(self.concentrated_nodes):

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

    def get_clusters(self):
        return self.concentrated_nodes

    def get_clusters_number(self):
        return self._scc_n

    def add_complex_node(self, id_):

        converted_id = list_to_dotted_string(id_)
        self.add_node(converted_id)
        self.nodes[converted_id]['index'] = -1
        self.nodes[converted_id]['low_link'] = -1
        self.nodes[converted_id]['id'] = -1
        return converted_id

    def add_edge_for_complex_nodes(self, id_1, id_2):

        converted_1 = self.add_complex_node(id_1)
        converted_2 = self.add_complex_node(id_2)
        self.add_edge(converted_1, converted_2)

    def sort_nodes(self):

        for node in [edge[0] for edge in self.edges]:
            if node not in self.blacklisted:
                self._perform_dfs(node)

        return self.blacklisted

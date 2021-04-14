import networkx as nx

from calculation.model.utils import list_to_dotted_string


class ComponentGraph(nx.Graph):

    def add_complex_node(self, id_):
        self.add_node(list_to_dotted_string(id_))

    def add_edge_for_complex_nodes(self, id_1, id_2):
        self.add_edge(
            list_to_dotted_string(id_1),
            list_to_dotted_string(id_2),
        )

    def fill_pulsar_weights(self):
        pulse = 0
        for node_from, node_to, data in self.edges(data=True):
            data['weight'] = pulse
            pulse = (pulse + 1) % 2

    # TODO actual implementation
    def get_scc_number(self):
        return 42

    # TODO actual implementation
    def get_concentrated_nodes(self):
        return self.nodes

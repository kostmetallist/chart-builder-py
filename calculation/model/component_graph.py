import networkx as nx


class ComponentGraph(nx.Graph):
    def fill_pulsar_weights(self):
        pulse = 0
        for node_from, node_to, data in self.edges(data=True):
            data['weight'] = pulse
            pulse = (pulse + 1) % 2

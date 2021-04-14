import logging
from enum import Enum, auto
from math import floor
from random import random

from calculation.model.utils import dotted_string_to_list

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CellStatus(Enum):
    ACTIVE = auto()
    DISCARDED = auto()


class ZoomableArea:

    def __init__(self, area, cells_by_x, cells_by_y, id_):

        self.sw_x = area[0]
        self.sw_y = area[1]
        self.ne_x = area[2]
        self.ne_y = area[3]
        self.cells_by_x = cells_by_x
        self.cells_by_y = cells_by_y
        self.id_ = id_

        self.cell_width = (self.ne_x-self.sw_x) / self.cells_by_x
        self.cell_height = (self.ne_y-self.sw_y) / self.cells_by_y
        self.status = CellStatus.ACTIVE
        self.cluster = 0

        self.children = []

        # if we really have a fragmentation
        if self.cells_by_x != 1 or self.cells_by_y != 1:
            self._initialize_children()

    # TODO numba @jit
    def _check_point_bounds(self, x, y): 
        return all([
            x > self.sw_x,
            x < self.ne_x,
            y > self.sw_y,
            y < self.ne_y,
        ])

    def _initialize_children(self):

        for j in range(self.cells_by_y):
            for i in range(self.cells_by_x):

                child_area = (
                    self.sw_x + i*self.cell_width,
                    self.sw_y + (self.cells_by_y-j-1) * self.cell_height,
                    self.sw_x + (i+1)*self.cell_width,
                    self.sw_y + (self.cells_by_y-j) * self.cell_height,
                )

                child = ZoomableArea(area, 1, 1,
                                     self.id_ + [j*self.cells_by_x + i])
                self.children.append(child)

    # TODO numba @jit
    def _set_cells_number(self, cells_by_x, cells_by_y):

        if self.cells_by_x == 1 and self.cells_by_y == 1:

            if cells_by_x != 1 or cells_by_y != 1:
                logging.warning('Incorrect values set for either cells_by_x '
                                f'({cells_by_x}) or cells_by_y ({cells_by_y})')
                return

            self.cells_by_x = cells_by_x
            self.cells_by_y = cells_by_y
            self.cell_width = (self.ne_x - self.sw_x) / self.cells_by_x
            self.cell_height  = (self.ne_y - self.sw_y) / self.cells_by_y

            self._initializeChildren()
    
    # TODO numba @jit
    def _get_cell_number(self, x, y):
        """
        Get cell number for given point (x, y).

        Counting up to down and left to right, i.e.

        ________________
        |    |    |    |
        |  0 |  1 |  2 |
        |____|____|____|
        |    |    |    |
        |  3 |  4 |  5 |
        |____|____|____|
        """

        if not self._check_point_bounds(x, y):
            logging.warning(f'Given point ({x}, {y}) is out of bounds')
            return

        i = int(floor((x - self.sw_x) / self.cell_width))
        j = int(floor((y - self.sw_y) / self.cell_height))

        return (self.cells_by_y - 1 - j) * self.cells_by_x + i

    def _get_random_points(self, amount, general_list, clusters_list=None):

        if not self.children and self.status is CellStatus.ACTIVE:

            area_points = []
            area_width = self.ne_x - self.sw_x
            area_height = self.ne_y - self.sw_y

            for i in range(amount):
                area_points.append((
                    self.sw_x + random() * area_width,
                    self.sw_y + random() * area_height
                ))

            general_list += area_points
            if clusters_list is not None:
                clusters_list.append(self.cluster)
        
        else:
            for child in self.children:
                child._get_random_points(amount, general_list, clusters_list)

    def get_cell_by_id(self, id_):

        parent = self

        for i in range(id_.size()):
            if not parent.children:
                if (i < len(id_) - 1):
                    logging.warning('get_cell_by_id reached end of '
                                    'fragmentation but `id_` is not over')
                return parent

            parent = parent.children[id_[i]]

    
    # TODO numba @jit
    def get_cell_by_point(self, x, y):
        """
        Note: this method returns appropriate ZoomableArea
        even if that cell is DISCARDED. You should check that
        case in the wrapping methods.
        """
        if not self.children:
            return self

        child = self.children[self._get_cell_number(x, y)]
        return child.get_cell_by_dot(x, y)

    def do_initial_fragmentation(self, component_graph):

        # component_graph must be root CellularArea
        for child in self.children:
            component_graph.add_complex_node(child.id_)

    def do_regular_fragmentation(self, component_graph):

        if not self.children and self.status is CellStatus.ACTIVE:

            self._set_cells_number(2, 2)

            for child in self.children:
                component_graph.add_complex_node(child.id_)

        else:
            # Even if we have terminated DISCARDED cell as `self`,
            #  it won't fragment further because of absence of children
            for child in self.children:
                child.do_regular_fragmentation(component_graph)

    def get_active_area(self, points_by_cell):

        general_list = []
        self._get_random_points(points_by_cell, general_list)
        return general_list

    def get_active_clustered_area(self, points_by_cell):

        general_list, clusters_list = [], []
        self._get_random_points(points_by_cell, general_list, clusters_list)
        return general_list, clusters_list

    def fill_symbolic_image(self, component_graph, x_mapping, y_mapping):

        nodes_collection = component_graph.nodes
        for node in nodes_collection:

            cell_id = dotted_string_to_list(node)
            zoomable_area = self.get_cell_by_id(cell_id)
            cell_points = []

            zoomable_area._get_random_points(100, cell_points)

            for point in cell_points:

                new_x = x_mapping(x, y)
                new_y = y_mapping(x, y)

                # In this case we do not registrating such link in graph
                if not self._check_point_bounds(new_x, new_y):
                    break

                # A cell which contains mapped point
                remote_cell = self.get_cell_by_point(new_x, new_y)

                if remote_cell.status is CellStatus.DISCARDED:
                    break

                component_graph.add_edge_for_complex_nodes(
                    cell_id,
                    remote_cell.id_
                )

    def mark_as_discarded(self, nodes):

        for node in nodes:
            self.get_cell_by_id(
                dotted_string_to_list(node)).status = CellStatus.DISCARDED

    def markup_entire_area(self, component_graph):

        print(f'Number of SCC: {component_graph.get_scc_number()}')
        i = 0

        for cluster in component_graph.get_concentrated_nodes():
            for node in cluster:
                id_ = dotted_string_to_list(node)
                if i > component_graph.get_scc_number() - 1: 
                    self.get_cell_by_id(id_).status = CellStatus.DISCARDED
                else:
                    self.get_cell_by_id(id_).cluster = i
            i += 1

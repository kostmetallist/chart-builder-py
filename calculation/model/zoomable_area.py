import logging
from enum import Enum, auto
from random import random

import numpy as np
from numba import jit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@jit(nopython=True)
def check_point_in_area(x, y,
                        area_sw_x, area_sw_y, area_ne_x, area_ne_y):
    # TODO experiment with performance of bidirected comparisons
    return x > area_sw_x \
        and x < area_ne_x \
        and y > area_sw_y \
        and y < area_ne_y


@jit(nopython=True, fastmath=True)
def get_cell_number_for_point(x, y,
                              area_sw_x, area_sw_y, area_ne_x, area_ne_y,
                              cells_by_x, cells_by_y):
    """
    Retrieve area's cell number for given point (x, y).

    Counting up to down and left to right, i.e.

    ________________
    |    |    |    |
    |  0 |  1 |  2 |
    |____|____|____|
    |    |    |    |
    |  3 |  4 |  5 |
    |____|____|____|
    """
    if not check_point_in_area(x, y, area_sw_x, area_sw_y, area_ne_x, area_ne_y):
        return -1

    cell_width = (area_ne_x - area_sw_x) / cells_by_x
    cell_height = (area_ne_y - area_sw_y) / cells_by_y

    i = np.int32(np.floor((x - area_sw_x) / cell_width))
    j = np.int32(np.floor((y - area_sw_y) / cell_height))

    return (cells_by_y - 1 - j) * cells_by_x + i


class CellStatus(Enum):
    ACTIVE = auto()
    DISCARDED = auto()


class ZoomableArea:

    def __init__(self, area_bounds, cells_by_x, cells_by_y, id_):

        self.sw_x = area_bounds[0]
        self.sw_y = area_bounds[1]
        self.ne_x = area_bounds[2]
        self.ne_y = area_bounds[3]
        self.cells_by_x = cells_by_x
        self.cells_by_y = cells_by_y
        self.id_ = id_

        self.cell_width = (self.ne_x - self.sw_x) / self.cells_by_x
        self.cell_height = (self.ne_y - self.sw_y) / self.cells_by_y
        self.status = CellStatus.ACTIVE
        self.cluster = 0

        self.children = []

        # if we really have a fragmentation
        if self.cells_by_x != 1 or self.cells_by_y != 1:
            self._initialize_children()

    def _initialize_children(self):

        for j in range(self.cells_by_y):
            for i in range(self.cells_by_x):

                child_area = (
                    self.sw_x + i * self.cell_width,
                    self.sw_y + (self.cells_by_y-j-1) * self.cell_height,
                    self.sw_x + (i+1) * self.cell_width,
                    self.sw_y + (self.cells_by_y-j) * self.cell_height,
                )

                child = ZoomableArea(child_area, 1, 1,
                                     self.id_ + (j*self.cells_by_x + i, ))
                self.children.append(child)

    def _set_cells_number(self, cells_by_x, cells_by_y):

        if self.cells_by_x == 1 and self.cells_by_y == 1:

            if cells_by_x == 1 and cells_by_y == 1:
                logging.warning('Incorrect values set for either cells_by_x '
                                f'({cells_by_x}) or cells_by_y ({cells_by_y})')
                return

            self.cells_by_x = cells_by_x
            self.cells_by_y = cells_by_y
            self.cell_width = (self.ne_x - self.sw_x) / self.cells_by_x
            self.cell_height = (self.ne_y - self.sw_y) / self.cells_by_y

            self._initialize_children()

    def get_active_area_points(self, cell_density, general_list, clusters_list=None):

        if not self.children and self.status is CellStatus.ACTIVE:

            area_points = []
            area_width = self.ne_x - self.sw_x
            area_height = self.ne_y - self.sw_y

            for i in range(cell_density):
                area_points.append((
                    self.sw_x + random() * area_width,
                    self.sw_y + random() * area_height
                ))

            general_list += area_points
            if clusters_list is not None:
                clusters_list.append(self.cluster)
        
        else:
            for child in self.children:
                child.get_active_area_points(
                    cell_density, general_list, clusters_list)

    def get_cell_by_id(self, id_):

        parent = self

        for i in range(len(id_)):
            if not parent.children:
                if i < len(id_) - 1:
                    logging.warning('get_cell_by_id reached end of '
                                    'fragmentation but `id_` is not over')
                return parent

            parent = parent.children[id_[i]]

        return parent

    def get_cell_by_point(self, x, y):
        """
        Note: this method returns appropriate ZoomableArea
        even if that cell is DISCARDED. You should check that
        case in the wrapping methods.
        """
        if not self.children:
            return self

        cell_number = get_cell_number_for_point(
            x, y,
            self.sw_x, self.sw_y, self.ne_x, self.ne_y,
            self.cells_by_x, self.cells_by_y
        )

        if cell_number == -1:
            logging.warning(f'Given point ({x}, {y}) is out of bounds')
            return

        child = self.children[cell_number]
        return child.get_cell_by_point(x, y)

    def do_initial_fragmentation(self, component_graph):

        # component_graph must be root ZoomableArea
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

    def fill_symbolic_image(self, component_graph, x_mapping, y_mapping):

        for node in component_graph.nodes:

            zoomable_area = self.get_cell_by_id(node)
            cell_points = []

            zoomable_area.get_active_area_points(100, cell_points, [])

            for point in cell_points:

                new_x = x_mapping(point[0], point[1])
                new_y = y_mapping(point[0], point[1])

                # In this case we do not registrating such link in graph
                if not check_point_in_area(
                        new_x, new_y,
                        self.sw_x, self.sw_y, self.ne_x, self.ne_y):
                    break

                # A cell which contains mapped point
                remote_cell = self.get_cell_by_point(new_x, new_y)

                if remote_cell.status is CellStatus.DISCARDED:
                    break

                component_graph.add_edge_for_complex_nodes(
                    node,
                    remote_cell.id_
                )

    def markup_entire_area(self, component_graph):

        clusters_num = 0
        ordered_components = list(sorted(
            component_graph.get_strongly_connected_components(),
            key=len,
            reverse=True))

        for i, component in enumerate(ordered_components):
            for node in component:

                if len(component) > 1:
                    self.get_cell_by_id(node).cluster = i
                    clusters_num += 1
                else:
                    self.get_cell_by_id(node).status = CellStatus.DISCARDED

        logging.debug(f'{clusters_num}/{len(ordered_components)} '
                      'components are clusters')

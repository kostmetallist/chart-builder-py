import logging

import numpy as np
from tqdm import tqdm

from calculation.model.component_graph import ComponentGraph
from calculation.model.zoomable_area import ZoomableArea

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _validate_args(x_mapping, y_mapping, area_bounds, cell_density, depth):

    if not callable(x_mapping):
        logging.error(f'`x_mapping` ({x_mapping}) is not a callable object; '
                      'expected lambda function')
        raise ValueError

    if not callable(y_mapping):
        logging.error(f'`y_mapping` ({y_mapping}) is not a callable object; '
                      'expected lambda function')
        raise ValueError

    if not hasattr(area_bounds, '__iter__') \
            or len(area_bounds) != 4 \
            or any([not isinstance(elem, float) for elem in area_bounds]):
        logging.error(f'Incorrect `area_bounds` format: {area_bounds}; '
                      'must be an iterable of four floats')
        raise ValueError

    if cell_density < 1:
        logging.error(f'Invalid `cell_density` number given: {cell_density}; '
                      'pass positive integer instead')
        raise ValueError

    if depth < 1:
        logging.error(f'Invalid `depth` number given: {depth}; '
                      'pass positive integer instead')
        raise ValueError


def condense_connected_components(x_mapping, y_mapping,
                                  area_bounds=(0, 0, 1, 1), cell_density=100,
                                  depth=5):

    try:
        _validate_args(x_mapping, y_mapping, area_bounds, cell_density, depth)
    except ValueError:
        logging.error('Aborting connected components localization...')
        return None

    cg_init = ComponentGraph()
    # TODO move cells_by_x, cells_by_y to settings
    area = ZoomableArea(area_bounds, 40, 40, [])

    area.do_initial_fragmentation(cg_init)
    area.fill_symbolic_image(cg_init, x_mapping, y_mapping)
    cg_init.run_tarjan()
    area.markup_entire_area(cg_init)

    for i in tqdm(range(depth)):

        cg = ComponentGraph()

        area.do_regular_fragmentation(cg)
        area.fill_symbolic_image(cg, x_mapping, y_mapping)
        cg.run_tarjan()
        area.markup_entire_area(cg)

        if i == depth - 1:

            condensed_cg = cg.generate_condensed_graph()
            sorted_reversed = condensed_cg.sort_nodes()
            order_list = []

            for node in sorted_reversed:
                if condensed_cg.nodes[node]['id'] < cg.get_clusters_number():
                    order_list.insert(0, node)

            print('Order of SCC:', *order_list, sep='\n')

    pre_result = area.get_active_clustered_area(cell_density)[0]
    xs = np.empty(len(pre_result), dtype=np.float32)
    ys = np.empty(len(pre_result), dtype=np.float32)
    for i, elem in enumerate(pre_result):
        xs[i] = elem[0]
        ys[i] = elem[1]

    return xs, ys

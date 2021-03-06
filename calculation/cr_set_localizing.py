import logging

import numpy as np
from tqdm import trange

from calculation.model.component_graph import ComponentGraph
from calculation.model.zoomable_area import ZoomableArea
from monitoring.decorators import capture_execution_time, dump_profile

logger = logging.getLogger()
logger.setLevel(logging.INFO)

INITIAL_FRAGMENTATION = (40, 40)


def _validate_args(x_mapping, y_mapping, area_bounds, cell_density, depth,
                   topsort_enabled):

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

    if not isinstance(topsort_enabled, bool):
        logging.error(f'Invalid `topsort_enabled` given: {topsort_enabled}; '
                      'pass boolean value instead')
        raise ValueError


@dump_profile
@capture_execution_time
def condense_connected_components(x_mapping, y_mapping,
                                  area_bounds=(0, 0, 1, 1), cell_density=100,
                                  depth=5, topsort_enabled=False):

    try:
        _validate_args(x_mapping, y_mapping, area_bounds, cell_density, depth,
                      topsort_enabled)
    except ValueError:
        logging.error('Aborting connected components localization...')
        return None

    cg_init = ComponentGraph()
    area = ZoomableArea(area_bounds, *INITIAL_FRAGMENTATION, tuple())

    area.do_initial_fragmentation(cg_init)
    area.fill_symbolic_image(cg_init, x_mapping, y_mapping)
    area.markup_entire_area(cg_init)

    components_order = []

    for i in trange(depth):

        cg = ComponentGraph()

        area.do_regular_fragmentation(cg)
        area.fill_symbolic_image(cg, x_mapping, y_mapping)
        area.markup_entire_area(cg)

        if topsort_enabled and i == depth - 1:

            logging.info('Launching topological sorting on the last layer...')
            condensed_cg = cg.generate_condensed_graph()
            sorted_reversed = condensed_cg.sort_nodes()
            dense_components = cg.dense_components

            for node in sorted_reversed:
                if condensed_cg.nodes[node]['group'] < len(dense_components):
                    components_order.insert(0, node)


    if topsort_enabled:
        print('Order of SCC:', *[x[0] for x in components_order], sep='\n')

    points = []
    area.get_active_area_points(cell_density, points)
    xs = np.empty(len(points), dtype=np.float32)
    ys = np.empty(len(points), dtype=np.float32)
    for i, elem in enumerate(points):
        xs[i] = elem[0]
        ys[i] = elem[1]

    return xs, ys

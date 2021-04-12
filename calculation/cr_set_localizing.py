import logging

import numpy as np
from tqdm import tqdm

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _validate_args(x_mapping, y_mapping, area, cell_density, depth):

    if not callable(x_mapping):
        logging.error(f'`x_mapping` ({x_mapping}) is not a callable object; '
                      'expected lambda function')
        raise ValueError

    if not callable(y_mapping):
        logging.error(f'`y_mapping` ({y_mapping}) is not a callable object; '
                      'expected lambda function')
        raise ValueError

    if not hasattr(area, '__iter__') \
            or len(area) != 4 \
            or any([not isinstance(elem, float) for elem in area]):
        logging.error(f'Incorrect `area` format: {area}; '
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


def condense_connected_components(x_mapping, y_mapping, area=(0, 0, 1, 1),
                                  cell_density=100, depth=5):

    try:
        _validate_args(x_mapping, y_mapping, area, cell_density, depth)
    except ValueError:
        logging.error('Aborting connected components localization...')
        return None

    # Dummy implementation
    xs_array = np.empty(cell_density, dtype=np.float32)
    ys_array = np.empty(cell_density, dtype=np.float32)

    return xs_array, ys_array

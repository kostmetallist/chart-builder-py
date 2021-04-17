import logging

import numpy as np
from tqdm import tqdm

from calculation.monitoring import capture_execution_time

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _validate_args(x_mapping, y_mapping, start_point, iterations):

    if not callable(x_mapping):
        logging.error(f'`x_mapping` ({x_mapping}) is not a callable object; '
                      'expected lambda function')
        raise ValueError

    if not callable(y_mapping):
        logging.error(f'`y_mapping` ({y_mapping}) is not a callable object; '
                      'expected lambda function')
        raise ValueError

    if not hasattr(start_point, '__iter__') \
            or len(start_point) != 2 \
            or any([not isinstance(elem, float) for elem in start_point]):
        logging.error(f'Incorrect `start_point` format: {start_point}; '
                      'must be an iterable of two floats')
        raise ValueError

    if iterations < 1:
        logging.error(f'Invalid `iterations` number given: {iterations}; '
                      'pass positive integer instead')
        raise ValueError


@capture_execution_time
def populate_2d_points(x_mapping, y_mapping, start_point=(.0, .0),
                       iterations=100):

    try:
        _validate_args(x_mapping, y_mapping, start_point, iterations)
    except ValueError:
        logging.error('Aborting arbitrary mapping construction...')
        return None

    xs_array = np.empty(iterations + 1, dtype=np.float32)
    ys_array = np.empty(iterations + 1, dtype=np.float32)

    x, y = start_point

    # TODO try to store everything in one array to grab as more elements 
    # as possible per cache line
    xs_array[0], ys_array[0] = x, y

    for i in tqdm(range(iterations)):
        x, y = x_mapping(x, y), y_mapping(x, y)
        xs_array[i + 1], ys_array[i + 1] = x, y

    logging.info('The mapping is ready')
    return xs_array, ys_array

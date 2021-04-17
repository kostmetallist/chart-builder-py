import logging
from time import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def capture_execution_time(f):

    def inner(*args, **kwargs):
        time_start = time()
        result = f(*args, **kwargs)
        logging.debug(f'Capturing execution time for {f.__name__}')
        logging.info(f'Elapsed time is {time() - time_start} sec')

        return result

    return inner

import logging
import os

from cProfile import Profile
from datetime import datetime
from io import StringIO
from pstats import Stats
from time import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PROFILE_DUMP_PATH = 'monitoring'


def capture_execution_time(f):

    def inner(*args, **kwargs):

        logging.debug(f'Capturing execution time for {f.__name__}...')
        time_start = time()
        result = f(*args, **kwargs)
        logging.info(f'Elapsed time is {time() - time_start} sec')

        return result

    return inner


def dump_profile(f):

    def inner(*args, **kwargs):
        
        logging.debug(f'Profiling {f.__name__}...')
        profile = Profile()
        profile.enable()
        result = f(*args, **kwargs)
        profile.disable()

        p_stats = Stats(profile, stream=StringIO()).sort_stats('cumulative')
        p_stats.dump_stats(os.path.join(
            PROFILE_DUMP_PATH, f'{int(datetime.utcnow().timestamp())}.dmp'))

        return result

    return inner

import logging

from sympy.parsing.sympy_parser import parse_expr
# from tqdm import tqdm

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODES = {
    1: 'ARBITRARY_MAPPING',
    2: 'CR_SET_LOCALIZING',
}


if __name__ == '__main__':

    chosen_mode = None
    while not chosen_mode:
        try:
            chosen_mode = int(input('\n'.join([
                'Select a mode to operate on:',
                "\n".join(["  {}: {}".format(x, MODES[x]) for x in MODES]),
                '>>> '])))

            if chosen_mode not in MODES:
                print('Invalid mode number, please try again')
                chosen_mode = None

        except ValueError:
            print('Not an integer has been specified, please try again')
            chosen_mode = None

    logging.info(f'Running {MODES[chosen_mode]}...')

    if chosen_mode == 1:
        f_expr = parse_expr(input('Input f(x, y): '))
        g_expr = parse_expr(input('Input g(x, y): '))
        logging.info(f'Evaluating {f_expr}, {g_expr}')

    elif chosen_mode == 2:
        pass

    logging.info('Shutting down...')

import logging

from sympy import lambdify
from sympy.abc import x, y
from sympy.parsing.sympy_parser import parse_expr
# from tqdm import tqdm

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODES = {
    1: 'ARBITRARY_MAPPING',
    2: 'CR_SET_LOCALIZING',
}


def parse_two_argument_function(expression: str):

    expr = parse_expr(expression)
    if any([atom.is_Symbol and atom != x and atom != y
            for atom in expr.atoms()]):

        print('Specified expression contains symbols other than x or y: '
              f'{expr}, please enter function depending only on x and y')
        return None

    return lambdify([x, y], expr, 'numpy')



def input_function_repeatedly(prompt: str):

    parsed_function = None
    while not parsed_function:
        entered_expression = input(prompt)
        parsed_function = parse_two_argument_function(entered_expression)

    return parsed_function



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
        f_lambda = input_function_repeatedly('Input f(x, y): ')
        g_lambda = input_function_repeatedly('Input g(x, y): ')
        logging.info(f'Evaluating {f_lambda}, {g_lambda}')

    elif chosen_mode == 2:
        pass

    logging.info('Shutting down...')
